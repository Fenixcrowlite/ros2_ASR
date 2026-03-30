"""Simple energy-based VAD segmenter node."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

import rclpy
from asr_config import resolve_profile, validate_runtime_payload
from asr_core.audio import pcm_rms, pcm_signed_from_encoding, sample_width_from_encoding
from asr_core.namespaces import TOPICS
from asr_core.shutdown import safe_shutdown_node, spin_node_until_shutdown
from asr_interfaces.msg import AudioChunk, AudioSegment, NodeStatus, SpeechActivity
from asr_interfaces.srv import ReconfigureRuntime
from rclpy.node import Node


class VadSegmenterNode(Node):
    def __init__(self) -> None:
        super().__init__("vad_segmenter_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("energy_threshold", 100)
        self.declare_parameter("pre_roll_ms", 250)
        self.declare_parameter("max_silence_ms", 700)
        self.declare_parameter("min_segment_ms", 400)
        self.declare_parameter("max_segment_ms", 2500)

        self.configs_root = str(self.get_parameter("configs_root").value)
        self.runtime_profile = str(self.get_parameter("runtime_profile").value)
        self.energy_threshold = int(self.get_parameter("energy_threshold").value)
        self.pre_roll_ms = int(self.get_parameter("pre_roll_ms").value)
        self.max_silence_ms = int(self.get_parameter("max_silence_ms").value)
        self.min_segment_ms = int(self.get_parameter("min_segment_ms").value)
        self.max_segment_ms = int(self.get_parameter("max_segment_ms").value)

        self.activity_pub = self.create_publisher(SpeechActivity, TOPICS["vad_activity"], 10)
        self.segment_pub = self.create_publisher(AudioSegment, TOPICS["speech_segments"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)
        self.subscription = self.create_subscription(
            AudioChunk,
            TOPICS["preprocessed_audio"],
            self._on_chunk,
            10,
        )
        self.reconfigure_srv = self.create_service(
            ReconfigureRuntime,
            "/asr/runtime/vad/reconfigure",
            self._on_reconfigure,
        )

        # These per-session buffers hold the simple VAD state machine:
        # recent silence, current segment bytes, metadata, and rolling pre-roll.
        self._buffers: dict[str, bytearray] = defaultdict(bytearray)
        self._segment_start: dict[str, Any] = {}
        self._segment_elapsed_ms: dict[str, int] = defaultdict(int)
        self._trailing_silence_ms: dict[str, int] = defaultdict(int)
        self._segment_index: dict[str, int] = defaultdict(int)
        self._segment_sample_rate: dict[str, int] = {}
        self._segment_channels: dict[str, int] = {}
        self._segment_encoding: dict[str, str] = {}
        self._segment_source_id: dict[str, str] = {}
        self._segment_metadata_ref: dict[str, str] = {}
        self._pre_roll_chunks: dict[str, deque[tuple[bytes, int]]] = defaultdict(deque)
        self._pre_roll_total_ms: dict[str, int] = defaultdict(int)
        self._last_error_code = ""
        self._last_error_message = ""
        self._status = "idle"
        self._last_update = self.get_clock().now()
        self._load_runtime_configuration(self.runtime_profile)
        self.status_timer = self.create_timer(1.0, self._publish_status)

    @staticmethod
    def _sample_width_bytes(encoding: str | None) -> int:
        return sample_width_from_encoding(encoding, default=2)

    @staticmethod
    def _segment_duration_ms(
        *, payload: bytes, sample_rate: int, channels: int, encoding: str
    ) -> int:
        sample_width_bytes = VadSegmenterNode._sample_width_bytes(encoding)
        return int(len(payload) / max(sample_rate * channels * sample_width_bytes, 1) * 1000)

    @staticmethod
    def _reset_session_state(node, session_id: str) -> None:
        node._buffers[session_id].clear()
        node._segment_start.pop(session_id, None)
        node._segment_elapsed_ms.pop(session_id, None)
        node._trailing_silence_ms.pop(session_id, None)
        node._segment_sample_rate.pop(session_id, None)
        node._segment_channels.pop(session_id, None)
        node._segment_encoding.pop(session_id, None)
        node._segment_source_id.pop(session_id, None)
        node._segment_metadata_ref.pop(session_id, None)
        VadSegmenterNode._clear_pre_roll(node, session_id)

    def _load_runtime_configuration(self, runtime_profile: str) -> str:
        profile_id = runtime_profile
        if profile_id.startswith("runtime/"):
            profile_id = profile_id.split("/", 1)[1]

        resolved = resolve_profile(
            profile_type="runtime",
            profile_id=profile_id,
            configs_root=self.configs_root,
        )
        runtime_cfg = resolved.data
        errors = validate_runtime_payload(runtime_cfg)
        if errors:
            raise ValueError("; ".join(errors))

        vad_cfg = runtime_cfg.get("vad", {})
        if not isinstance(vad_cfg, dict):
            raise ValueError("runtime.vad must be an object")

        self.runtime_profile = profile_id
        self.energy_threshold = int(
            vad_cfg.get("energy_threshold", self.energy_threshold) or self.energy_threshold
        )
        self.pre_roll_ms = int(vad_cfg.get("pre_roll_ms", self.pre_roll_ms) or self.pre_roll_ms)
        self.max_silence_ms = int(
            vad_cfg.get("max_silence_ms", self.max_silence_ms) or self.max_silence_ms
        )
        self.min_segment_ms = int(
            vad_cfg.get("min_segment_ms", self.min_segment_ms) or self.min_segment_ms
        )
        self.max_segment_ms = int(
            vad_cfg.get("max_segment_ms", self.max_segment_ms) or self.max_segment_ms
        )
        self._status = "ready"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        return resolved.snapshot_path

    def _pcm_duration_ms(self, msg: AudioChunk, payload: bytes) -> int:
        if not payload:
            return 0
        sample_rate = int(msg.sample_rate) or 16000
        channels = int(msg.channels) or 1
        sample_width = VadSegmenterNode._sample_width_bytes(msg.encoding)
        bytes_per_second = max(sample_rate * channels * sample_width, 1)
        return int(len(payload) / float(bytes_per_second) * 1000.0)

    def _append_pre_roll(self, msg: AudioChunk, payload: bytes) -> None:
        # Keep a small amount of audio before speech starts so the provider does
        # not lose the first syllable of an utterance.
        if self.pre_roll_ms <= 0 or not payload:
            return
        session_id = msg.session_id
        duration_ms = self._pcm_duration_ms(msg, payload)
        if duration_ms <= 0:
            return
        self._pre_roll_chunks[session_id].append((payload, duration_ms))
        self._pre_roll_total_ms[session_id] += duration_ms
        while (
            self._pre_roll_total_ms[session_id] > self.pre_roll_ms
            and len(self._pre_roll_chunks[session_id]) > 1
        ):
            _, removed_ms = self._pre_roll_chunks[session_id].popleft()
            self._pre_roll_total_ms[session_id] -= removed_ms

    def _consume_pre_roll(self, session_id: str) -> bytes:
        chunks = self._pre_roll_chunks.get(session_id)
        if not chunks:
            return b""
        payload = b"".join(chunk for chunk, _ in chunks)
        chunks.clear()
        self._pre_roll_total_ms[session_id] = 0
        return payload

    def _clear_pre_roll(self, session_id: str) -> None:
        self._pre_roll_chunks.pop(session_id, None)
        self._pre_roll_total_ms.pop(session_id, None)

    def _on_chunk(self, msg: AudioChunk) -> None:
        # This node intentionally uses a transparent energy-based VAD. It is not
        # the smartest detector, but it is easy to understand and debug.
        now = self.get_clock().now()
        data = bytes(msg.data)
        chunk_duration_ms = self._pcm_duration_ms(msg, data)
        sample_width = VadSegmenterNode._sample_width_bytes(msg.encoding)
        signed = pcm_signed_from_encoding(msg.encoding, default=sample_width != 1)
        energy = float(pcm_rms(data, sample_width=sample_width, signed=signed)) if data else 0.0
        speech_active = energy >= self.energy_threshold
        should_flush = False
        preserve_silence_as_pre_roll = False
        flush_reason = ""

        activity = SpeechActivity()
        activity.header.stamp = now.to_msg()
        activity.session_id = msg.session_id
        activity.speech_active = bool(speech_active)
        activity.energy_level = float(energy)
        activity.probability = 1.0 if speech_active else 0.0
        activity.state = "speech" if speech_active else "silence"
        activity.details = f"threshold={self.energy_threshold}"
        self.activity_pub.publish(activity)

        if speech_active:
            if msg.session_id not in self._segment_start:
                self._segment_start[msg.session_id] = now
                self._segment_sample_rate[msg.session_id] = int(msg.sample_rate) or 16000
                self._segment_channels[msg.session_id] = int(msg.channels) or 1
                self._segment_encoding[msg.session_id] = str(msg.encoding or "pcm_s16le")
                self._segment_source_id[msg.session_id] = str(msg.source_id or "")
                self._segment_metadata_ref[msg.session_id] = str(msg.metadata_ref or "")
                pre_roll = self._consume_pre_roll(msg.session_id)
                if pre_roll:
                    self._buffers[msg.session_id].extend(pre_roll)
                    self._segment_elapsed_ms[msg.session_id] += (
                        VadSegmenterNode._segment_duration_ms(
                            payload=pre_roll,
                            sample_rate=self._segment_sample_rate[msg.session_id],
                            channels=self._segment_channels[msg.session_id],
                            encoding=self._segment_encoding[msg.session_id],
                        )
                    )
            self._segment_sample_rate[msg.session_id] = int(
                msg.sample_rate
            ) or self._segment_sample_rate.get(msg.session_id, 16000)
            self._segment_channels[msg.session_id] = int(
                msg.channels
            ) or self._segment_channels.get(msg.session_id, 1)
            self._segment_encoding[msg.session_id] = str(
                msg.encoding or self._segment_encoding.get(msg.session_id, "")
            )
            self._segment_source_id[msg.session_id] = str(
                msg.source_id or self._segment_source_id.get(msg.session_id, "")
            )
            self._segment_metadata_ref[msg.session_id] = str(
                msg.metadata_ref or self._segment_metadata_ref.get(msg.session_id, "")
            )
            self._buffers[msg.session_id].extend(data)
            self._segment_elapsed_ms[msg.session_id] += chunk_duration_ms
            self._trailing_silence_ms[msg.session_id] = 0
        else:
            if not self._buffers[msg.session_id]:
                self._append_pre_roll(msg, data)
            elif chunk_duration_ms > 0:
                trailing_silence_ms = self._trailing_silence_ms[msg.session_id] + chunk_duration_ms
                if self.max_silence_ms >= 0 and trailing_silence_ms > self.max_silence_ms:
                    should_flush = True
                    preserve_silence_as_pre_roll = bool(data)
                    flush_reason = "silence"
                else:
                    self._buffers[msg.session_id].extend(data)
                    self._segment_elapsed_ms[msg.session_id] += chunk_duration_ms
                    self._trailing_silence_ms[msg.session_id] = trailing_silence_ms

        if self._buffers[msg.session_id]:
            segment_duration_ms = self._segment_elapsed_ms[msg.session_id]
            if self.max_segment_ms > 0 and segment_duration_ms >= self.max_segment_ms:
                should_flush = True
                flush_reason = flush_reason or "max_segment"
            if msg.is_last_chunk:
                should_flush = True
                flush_reason = flush_reason or "terminal"

        if should_flush:
            self._flush_segment(msg, now, reason=flush_reason or "threshold")
            if preserve_silence_as_pre_roll:
                self._append_pre_roll(msg, data)

        self._status = "ready" if msg.is_last_chunk else "running"
        self._last_update = self.get_clock().now()

    def _flush_segment(self, msg: AudioChunk, end_time, *, reason: str = "threshold") -> None:
        payload = bytes(self._buffers[msg.session_id])
        if not payload:
            return

        sample_rate = int(
            self._segment_sample_rate.get(msg.session_id, msg.sample_rate or 16000) or 16000
        )
        channels = int(self._segment_channels.get(msg.session_id, msg.channels or 1) or 1)
        encoding = str(
            self._segment_encoding.get(msg.session_id, msg.encoding or "pcm_s16le") or "pcm_s16le"
        )
        source_id = str(self._segment_source_id.get(msg.session_id, msg.source_id) or "")
        metadata_ref = str(self._segment_metadata_ref.get(msg.session_id, msg.metadata_ref) or "")

        duration_ms = VadSegmenterNode._segment_duration_ms(
            payload=payload,
            sample_rate=sample_rate,
            channels=channels,
            encoding=encoding,
        )
        if duration_ms < self.min_segment_ms:
            # Drop tiny bursts so downstream providers are not spammed with
            # micro-segments caused by taps, clicks, or breathing noise.
            VadSegmenterNode._reset_session_state(self, msg.session_id)
            return

        segment = AudioSegment()
        segment.header.stamp = end_time.to_msg()
        segment.session_id = msg.session_id
        segment.segment_id = f"{msg.session_id}_seg_{self._segment_index[msg.session_id]}"
        segment.source_id = source_id
        segment.start_time = self._segment_start.get(msg.session_id, end_time).to_msg()
        segment.end_time = end_time.to_msg()
        segment.sample_rate = sample_rate
        segment.channels = channels
        segment.encoding = encoding
        segment.data = list(payload)
        segment.metadata_ref = metadata_ref
        self.segment_pub.publish(segment)
        logger = getattr(self, "get_logger", None)
        if callable(logger):
            logger().info(
                "VAD flushed segment "
                f"session_id={msg.session_id} segment_id={segment.segment_id} "
                f"duration_ms={duration_ms} bytes={len(payload)} reason={reason}"
            )

        self._segment_index[msg.session_id] += 1
        VadSegmenterNode._reset_session_state(self, msg.session_id)

    def _on_reconfigure(
        self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response
    ):
        try:
            snapshot_path = self._load_runtime_configuration(
                request.runtime_profile or self.runtime_profile
            )
            response.success = True
            response.message = "VAD reconfigured"
            response.resolved_config_ref = snapshot_path
        except Exception as exc:
            self._status = "error"
            self._last_error_code = "vad_reconfigure_failed"
            self._last_error_message = str(exc)
            self._last_update = self.get_clock().now()
            response.success = False
            response.message = str(exc)
            response.resolved_config_ref = ""
        return response

    def _publish_status(self) -> None:
        msg = NodeStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.node_name = self.get_name()
        msg.lifecycle_state = "active"
        msg.health = "ok" if not self._last_error_code else "degraded"
        msg.status_message = (
            f"{self._status} threshold={self.energy_threshold} "
            f"silence_ms={self.max_silence_ms} max_segment_ms={self.max_segment_ms}"
        )
        msg.ready = self._status in {"ready", "running"}
        msg.last_error_code = self._last_error_code
        msg.last_error_message = self._last_error_message
        msg.last_update = self._last_update.to_msg()
        self.node_status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = VadSegmenterNode()
    try:
        spin_node_until_shutdown(node=node, rclpy_module=rclpy)
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
