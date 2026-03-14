"""Simple energy-based VAD segmenter node."""

from __future__ import annotations

import audioop
from collections import defaultdict

import rclpy
from asr_config import resolve_profile, validate_runtime_payload
from asr_core.namespaces import TOPICS
from asr_core.shutdown import safe_shutdown_node
from asr_interfaces.msg import AudioChunk, AudioSegment, NodeStatus, SpeechActivity
from asr_interfaces.srv import ReconfigureRuntime
from rclpy.node import Node


class VadSegmenterNode(Node):
    def __init__(self) -> None:
        super().__init__("vad_segmenter_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("energy_threshold", 500)
        self.declare_parameter("max_silence_ms", 700)
        self.declare_parameter("min_segment_ms", 400)
        self.declare_parameter("max_segment_ms", 2500)

        self.configs_root = str(self.get_parameter("configs_root").value)
        self.runtime_profile = str(self.get_parameter("runtime_profile").value)
        self.energy_threshold = int(self.get_parameter("energy_threshold").value)
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

        self._buffers: dict[str, bytearray] = defaultdict(bytearray)
        self._segment_start: dict[str, any] = {}
        self._last_speech_ms: dict[str, int] = defaultdict(lambda: 0)
        self._segment_index: dict[str, int] = defaultdict(int)
        self._segment_sample_rate: dict[str, int] = {}
        self._segment_channels: dict[str, int] = {}
        self._segment_encoding: dict[str, str] = {}
        self._segment_source_id: dict[str, str] = {}
        self._segment_metadata_ref: dict[str, str] = {}
        self._last_error_code = ""
        self._last_error_message = ""
        self._status = "idle"
        self._last_update = self.get_clock().now()
        self._load_runtime_configuration(self.runtime_profile)
        self.status_timer = self.create_timer(1.0, self._publish_status)

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
        self.energy_threshold = int(vad_cfg.get("energy_threshold", self.energy_threshold) or self.energy_threshold)
        self.max_silence_ms = int(vad_cfg.get("max_silence_ms", self.max_silence_ms) or self.max_silence_ms)
        self.min_segment_ms = int(vad_cfg.get("min_segment_ms", self.min_segment_ms) or self.min_segment_ms)
        self.max_segment_ms = int(vad_cfg.get("max_segment_ms", self.max_segment_ms) or self.max_segment_ms)
        self._status = "ready"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        return resolved.snapshot_path

    def _on_chunk(self, msg: AudioChunk) -> None:
        now = self.get_clock().now()
        now_ms = now.nanoseconds // 1_000_000
        data = bytes(msg.data)
        energy = float(audioop.rms(data, 2)) if data else 0.0
        speech_active = energy >= self.energy_threshold

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
            self._segment_sample_rate[msg.session_id] = int(msg.sample_rate) or self._segment_sample_rate.get(
                msg.session_id, 16000
            )
            self._segment_channels[msg.session_id] = int(msg.channels) or self._segment_channels.get(
                msg.session_id, 1
            )
            self._segment_encoding[msg.session_id] = str(msg.encoding or self._segment_encoding.get(msg.session_id, ""))
            self._segment_source_id[msg.session_id] = str(msg.source_id or self._segment_source_id.get(msg.session_id, ""))
            self._segment_metadata_ref[msg.session_id] = str(
                msg.metadata_ref or self._segment_metadata_ref.get(msg.session_id, "")
            )
            self._buffers[msg.session_id].extend(data)
            self._last_speech_ms[msg.session_id] = int(now_ms)
        else:
            silence_ms = int(now_ms) - int(self._last_speech_ms[msg.session_id])
            if self._buffers[msg.session_id] and silence_ms <= self.max_silence_ms:
                self._buffers[msg.session_id].extend(data)

        should_flush = False
        if self._buffers[msg.session_id]:
            silence_ms = int(now_ms) - int(self._last_speech_ms[msg.session_id])
            segment_start = self._segment_start.get(msg.session_id)
            segment_duration_ms = (
                int((now.nanoseconds - segment_start.nanoseconds) / 1_000_000)
                if segment_start is not None
                else 0
            )
            if silence_ms > self.max_silence_ms:
                should_flush = True
            if self.max_segment_ms > 0 and segment_duration_ms >= self.max_segment_ms:
                should_flush = True
            if msg.is_last_chunk:
                should_flush = True

        if should_flush:
            self._flush_segment(msg, now)

        self._status = "ready" if msg.is_last_chunk else "running"
        self._last_update = self.get_clock().now()

    def _flush_segment(self, msg: AudioChunk, end_time) -> None:
        payload = bytes(self._buffers[msg.session_id])
        if not payload:
            return

        sample_rate = int(self._segment_sample_rate.get(msg.session_id, msg.sample_rate or 16000) or 16000)
        channels = int(self._segment_channels.get(msg.session_id, msg.channels or 1) or 1)
        encoding = str(self._segment_encoding.get(msg.session_id, msg.encoding or "pcm_s16le") or "pcm_s16le")
        source_id = str(self._segment_source_id.get(msg.session_id, msg.source_id) or "")
        metadata_ref = str(self._segment_metadata_ref.get(msg.session_id, msg.metadata_ref) or "")

        sample_width_bytes = 2
        if encoding.endswith("u8"):
            sample_width_bytes = 1
        duration_ms = int(len(payload) / max(sample_rate * channels * sample_width_bytes, 1) * 1000)
        if duration_ms < self.min_segment_ms:
            self._buffers[msg.session_id].clear()
            self._segment_start.pop(msg.session_id, None)
            self._segment_sample_rate.pop(msg.session_id, None)
            self._segment_channels.pop(msg.session_id, None)
            self._segment_encoding.pop(msg.session_id, None)
            self._segment_source_id.pop(msg.session_id, None)
            self._segment_metadata_ref.pop(msg.session_id, None)
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

        self._segment_index[msg.session_id] += 1
        self._buffers[msg.session_id].clear()
        self._segment_start.pop(msg.session_id, None)
        self._segment_sample_rate.pop(msg.session_id, None)
        self._segment_channels.pop(msg.session_id, None)
        self._segment_encoding.pop(msg.session_id, None)
        self._segment_source_id.pop(msg.session_id, None)
        self._segment_metadata_ref.pop(msg.session_id, None)

    def _on_reconfigure(self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response):
        try:
            snapshot_path = self._load_runtime_configuration(request.runtime_profile or self.runtime_profile)
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
            f"{self._status} threshold={self.energy_threshold} silence_ms={self.max_silence_ms} max_segment_ms={self.max_segment_ms}"
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
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
