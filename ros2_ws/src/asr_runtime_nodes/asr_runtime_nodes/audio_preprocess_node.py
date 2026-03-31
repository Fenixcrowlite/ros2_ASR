"""Audio preprocessing node: mono conversion, resample, normalization."""

from __future__ import annotations

from array import array
from collections import defaultdict

import rclpy
from asr_config import resolve_profile, validate_runtime_payload
from asr_core.audio import (
    pcm_max_abs,
    pcm_peak_limit,
    pcm_resample_linear,
    pcm_scale,
    pcm_signed_from_encoding,
    pcm_to_mono,
    sample_width_from_encoding,
)
from asr_core.namespaces import TOPICS
from asr_core.shutdown import safe_shutdown_node, spin_node_until_shutdown
from asr_interfaces.msg import AudioChunk, NodeStatus
from asr_interfaces.srv import ReconfigureRuntime
from rclpy.node import Node

from asr_runtime_nodes.transport import (
    decode_transport_metadata,
    delivery_latency_ms,
    encode_transport_metadata,
    sequence_gap,
    stamp_to_ns,
)


class AudioPreprocessNode(Node):
    def __init__(self) -> None:
        super().__init__("audio_preprocess_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("target_sample_rate_hz", 16000)
        self.declare_parameter("normalize", True)
        self.declare_parameter("mono", True)

        self.configs_root = str(self.get_parameter("configs_root").value)
        self.runtime_profile = str(self.get_parameter("runtime_profile").value)
        self.target_sample_rate_hz = int(self.get_parameter("target_sample_rate_hz").value)
        self.normalize = bool(self.get_parameter("normalize").value)
        self.force_mono = bool(self.get_parameter("mono").value)

        self.publisher = self.create_publisher(AudioChunk, TOPICS["preprocessed_audio"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)
        self.subscription = self.create_subscription(
            AudioChunk,
            TOPICS["raw_audio"],
            self._on_chunk,
            10,
        )
        self.reconfigure_srv = self.create_service(
            ReconfigureRuntime,
            "/asr/runtime/preprocess/reconfigure",
            self._on_reconfigure,
        )

        self._last_error_code = ""
        self._last_error_message = ""
        self._status = "idle"
        self._last_update = self.get_clock().now()
        self._session_output_rate: dict[str, int] = defaultdict(lambda: self.target_sample_rate_hz)
        self._session_output_channels: dict[str, int] = defaultdict(lambda: 1)
        self._last_raw_sequence: dict[str, int] = defaultdict(lambda: -1)
        self._raw_chunks_in = 0
        self._raw_chunks_out = 0
        self._raw_sequence_gaps = 0
        self._last_raw_delivery_ms = 0.0
        self._max_raw_delivery_ms = 0.0
        self._load_runtime_configuration(self.runtime_profile)
        self.status_timer = self.create_timer(1.0, self._publish_status)

    def _load_runtime_configuration(self, runtime_profile: str) -> str:
        # Preprocess settings live in the runtime profile because they shape the
        # audio contract expected by later nodes and providers.
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

        preprocess_cfg = runtime_cfg.get("preprocess", {})
        if not isinstance(preprocess_cfg, dict):
            raise ValueError("runtime.preprocess must be an object")

        self.runtime_profile = profile_id
        self.target_sample_rate_hz = int(
            preprocess_cfg.get("target_sample_rate_hz", self.target_sample_rate_hz)
            or self.target_sample_rate_hz
        )
        self.normalize = bool(preprocess_cfg.get("normalize", self.normalize))
        self.force_mono = bool(preprocess_cfg.get("mono", self.force_mono))
        self._status = "ready"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        return resolved.snapshot_path

    def _on_chunk(self, msg: AudioChunk) -> None:
        now = self.get_clock().now()
        now_ns = int(getattr(now, "nanoseconds", 0) or 0)
        transport_meta = decode_transport_metadata(getattr(msg.header, "frame_id", ""))
        raw_sequence = int(transport_meta.get("raw_sequence", -1) or -1)
        previous_raw_sequence = self._last_raw_sequence.get(msg.session_id, -1)
        self._raw_sequence_gaps += sequence_gap(previous_raw_sequence, raw_sequence)
        if raw_sequence >= 0:
            self._last_raw_sequence[msg.session_id] = raw_sequence
        raw_delivery_ms = delivery_latency_ms(now_ns=now_ns, stamp=msg.header.stamp)
        self._raw_chunks_in += 1
        self._last_raw_delivery_ms = raw_delivery_ms
        self._max_raw_delivery_ms = max(self._max_raw_delivery_ms, raw_delivery_ms)
        data = bytes(msg.data)
        out_channels = int(msg.channels) or 1
        out_sample_rate = int(msg.sample_rate) or self.target_sample_rate_hz
        sample_width = sample_width_from_encoding(msg.encoding, default=2)
        signed = pcm_signed_from_encoding(msg.encoding, default=sample_width != 1)

        # Collapse stereo to mono when requested so every downstream provider
        # sees a simpler, predictable channel layout.
        if data and self.force_mono and int(msg.channels) == 2:
            data = pcm_to_mono(
                data,
                sample_width=sample_width,
                channels=2,
                signed=signed,
                left_gain=0.5,
                right_gain=0.5,
            )
            out_channels = 1
        elif self.force_mono and out_channels > 1 and not data:
            out_channels = 1

        # Resample early so VAD and provider code do not need to handle many
        # different input sample rates.
        if data and out_sample_rate != self.target_sample_rate_hz:
            data = pcm_resample_linear(
                data,
                sample_width=sample_width,
                channels=out_channels,
                source_rate_hz=out_sample_rate,
                target_rate_hz=self.target_sample_rate_hz,
                signed=signed,
            )
            out_sample_rate = int(self.target_sample_rate_hz)
        elif not data:
            # Preserve the last known output format for the closing "empty"
            # chunk that marks end-of-stream.
            out_sample_rate = int(
                self._session_output_rate.get(msg.session_id, self.target_sample_rate_hz)
            )
            out_channels = int(self._session_output_channels.get(msg.session_id, out_channels or 1))

        if data and self.normalize:
            # Soft normalization improves consistency without clipping.
            max_val = pcm_max_abs(data, sample_width=sample_width, signed=signed)
            if max_val > 0:
                peak_limit = float(pcm_peak_limit(sample_width, signed=signed))
                scale = min(1.0, (0.9 * peak_limit) / float(max_val))
                data = pcm_scale(data, sample_width=sample_width, factor=scale, signed=signed)

        out = AudioChunk()
        out.header = msg.header
        out.header.stamp = now.to_msg()
        out.header.frame_id = encode_transport_metadata(
            {
                **transport_meta,
                "stage": "preprocessed_audio",
                "preprocessed_sequence": self._raw_chunks_out,
                "published_ns": stamp_to_ns(out.header.stamp),
                "topic_delivery_ms": raw_delivery_ms,
                "sequence_gap_count": self._raw_sequence_gaps,
            }
        )
        out.session_id = msg.session_id
        out.source_id = msg.source_id
        out.sample_rate = out_sample_rate
        out.channels = out_channels
        out.encoding = msg.encoding
        out.is_last_chunk = msg.is_last_chunk
        out.data = array("B", data)
        out.metadata_ref = msg.metadata_ref
        self.publisher.publish(out)
        self._raw_chunks_out += 1
        self._session_output_rate[msg.session_id] = out_sample_rate
        self._session_output_channels[msg.session_id] = out_channels
        if msg.is_last_chunk:
            self._session_output_rate.pop(msg.session_id, None)
            self._session_output_channels.pop(msg.session_id, None)
            self._last_raw_sequence.pop(msg.session_id, None)
        self._status = "ready" if msg.is_last_chunk else "running"
        self._last_update = self.get_clock().now()

    def _on_reconfigure(
        self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response
    ):
        try:
            snapshot_path = self._load_runtime_configuration(
                request.runtime_profile or self.runtime_profile
            )
            response.success = True
            response.message = "Audio preprocess reconfigured"
            response.resolved_config_ref = snapshot_path
        except Exception as exc:
            self._status = "error"
            self._last_error_code = "preprocess_reconfigure_failed"
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
            f"{self._status} sample_rate={self.target_sample_rate_hz} "
            f"normalize={self.normalize} mono={self.force_mono} "
            f"raw_in={self._raw_chunks_in} raw_out={self._raw_chunks_out} "
            f"raw_gap={self._raw_sequence_gaps} "
            f"raw_delivery_ms={self._last_raw_delivery_ms:.3f}/{self._max_raw_delivery_ms:.3f}"
        )
        msg.ready = self._status in {"ready", "running"}
        msg.last_error_code = self._last_error_code
        msg.last_error_message = self._last_error_message
        msg.last_update = self._last_update.to_msg()
        self.node_status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = AudioPreprocessNode()
    try:
        spin_node_until_shutdown(node=node, rclpy_module=rclpy)
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
