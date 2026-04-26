"""Main ROS2 ASR node.

Responsibilities:
1. Expose one-shot service and long-running action.
2. Subscribe to live audio chunks and run live streaming recognition.
3. Publish normalized text + metrics topics.
4. Provide runtime backend status and backend switching.
"""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Any

import rclpy
from asr_core.audio import wav_pcm_chunks
from asr_core.config import load_runtime_config
from asr_core.factory import create_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse
from asr_core.ros_parameters import (
    parameter_bool,
    parameter_float,
    parameter_int,
    parameter_string,
)
from asr_interfaces.action import Transcribe
from asr_interfaces.msg import AsrMetrics, AsrResult
from asr_interfaces.srv import GetAsrStatus, RecognizeOnce, SetAsrBackend
from asr_metrics.collector import MetricsCollector
from asr_metrics.system import collect_cpu_ram, collect_gpu
from builtin_interfaces.msg import Time as RosTime
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.action import ActionServer, CancelResponse
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import UInt8MultiArray

from asr_ros.converters import build_metrics_msg, to_asr_result_msg
from asr_ros.shutdown import safe_shutdown_node


def _coerce_int_param(
    raw: Any,
    *,
    name: str,
    default: int,
    min_value: int,
    logger: Any,
) -> int:
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid parameter '{name}={raw}', expected integer >= {min_value}. "
            f"Using default {default}."
        )
        return default
    if value < min_value:
        logger.warning(
            f"Out-of-range parameter '{name}={value}', expected >= {min_value}. "
            f"Using default {default}."
        )
        return default
    return value


def _coerce_float_param(
    raw: Any,
    *,
    name: str,
    default: float,
    min_value: float,
    logger: Any,
) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid parameter '{name}={raw}', expected float >= {min_value}. "
            f"Using default {default}."
        )
        return default
    if value < min_value:
        logger.warning(
            f"Out-of-range parameter '{name}={value}', expected >= {min_value}. "
            f"Using default {default}."
        )
        return default
    return value


def _preview_text(value: str, limit: int = 160) -> str:
    """Return compact one-line preview used in metrics payload."""
    compact = " ".join(value.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: max(limit - 3, 0)] + "..."


class AsrServerNode(Node):
    """Serve legacy ASR services/actions and publish recognition results.

    Published topics:
    - `/asr/text` (`asr_interfaces/AsrResult`)
    - `/asr/metrics` (`asr_interfaces/AsrMetrics`)

    Subscribed topics:
    - `/asr/audio_chunks` (`std_msgs/UInt8MultiArray`)

    Services/actions:
    - `/asr/recognize_once`
    - `/asr/set_backend`
    - `/asr/get_status`
    - `/asr/transcribe`

    Parameters:
    - `config`, `backend`, `language`, `model`, `region`
    - `chunk_sec`, `sample_rate`
    - `live_stream_enabled`, `live_flush_timeout_sec`
    """

    def __init__(self) -> None:
        super().__init__("asr_server_node")
        numeric_descriptor = ParameterDescriptor(dynamic_typing=True)
        # Generic runtime parameters; empty values mean "take from YAML config".
        self.declare_parameter("config", "configs/default.yaml")
        self.declare_parameter("backend", "")
        self.declare_parameter("language", "")
        self.declare_parameter("model", "")
        self.declare_parameter("region", "")
        self.declare_parameter("chunk_sec", 0.0, descriptor=numeric_descriptor)
        self.declare_parameter("sample_rate", 0, descriptor=numeric_descriptor)
        self.declare_parameter("live_stream_enabled", True)
        self.declare_parameter("live_flush_timeout_sec", 1.0, descriptor=numeric_descriptor)

        self.config_path = parameter_string(self, "config")
        # Merge default config + optional local commercial overlay.
        self.runtime_cfg = load_runtime_config(self.config_path, "configs/commercial.yaml")
        self.lock = threading.Lock()

        self.backend_name = str(
            parameter_string(self, "backend")
            or self.runtime_cfg.get("asr", {}).get("backend", "mock")
        )
        self.language = str(
            parameter_string(self, "language")
            or self.runtime_cfg.get("asr", {}).get("language", "en-US")
        )
        self.language = normalize_language_code(self.language, fallback="en-US")
        self.model = str(
            parameter_string(self, "model") or self.runtime_cfg.get("asr", {}).get("model", "")
        )
        self.region = str(
            parameter_string(self, "region") or self.runtime_cfg.get("asr", {}).get("region", "")
        )
        chunk_cfg_default = _coerce_float_param(
            self.runtime_cfg.get("benchmark", {}).get("chunk_sec", 0.8),
            name="benchmark.chunk_sec",
            default=0.8,
            min_value=0.1,
            logger=self.get_logger(),
        )
        chunk_param = _coerce_float_param(
            parameter_float(self, "chunk_sec"),
            name="chunk_sec",
            default=0.0,
            min_value=0.0,
            logger=self.get_logger(),
        )
        self.chunk_sec = chunk_param if chunk_param > 0 else chunk_cfg_default
        sample_rate_cfg_default = _coerce_int_param(
            self.runtime_cfg.get("asr", {}).get("sample_rate", 16000),
            name="asr.sample_rate",
            default=16000,
            min_value=8000,
            logger=self.get_logger(),
        )
        sample_rate_param = _coerce_int_param(
            parameter_int(self, "sample_rate"),
            name="sample_rate",
            default=0,
            min_value=0,
            logger=self.get_logger(),
        )
        self.sample_rate = sample_rate_param if sample_rate_param > 0 else sample_rate_cfg_default
        self.live_stream_enabled = parameter_bool(self, "live_stream_enabled", default=True)
        self.live_flush_timeout_sec = _coerce_float_param(
            parameter_float(self, "live_flush_timeout_sec"),
            name="live_flush_timeout_sec",
            default=1.0,
            min_value=0.0,
            logger=self.get_logger(),
        )
        self._live_lock = threading.Lock()
        self._live_chunks: list[bytes] = []
        self._live_last_chunk_ts: float = 0.0
        self._live_capture_start: RosTime | None = None
        self._live_capture_end: RosTime | None = None
        self._live_processing = False

        # Metric collector is reused for service/action/live-topic flows.
        self.collector = MetricsCollector(
            pricing_per_minute=self.runtime_cfg.get("benchmark", {}).get("pricing", {})
        )
        self.backend = self._create_backend(self.backend_name)

        # Transient local QoS keeps last message for late subscribers.
        latched_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.text_pub = self.create_publisher(AsrResult, "/asr/text", latched_qos)
        self.metrics_pub = self.create_publisher(AsrMetrics, "/asr/metrics", latched_qos)

        self.recognize_srv = self.create_service(
            RecognizeOnce, "/asr/recognize_once", self._on_recognize_once
        )
        self.set_backend_srv = self.create_service(
            SetAsrBackend, "/asr/set_backend", self._on_set_backend
        )
        self.get_status_srv = self.create_service(
            GetAsrStatus, "/asr/get_status", self._on_get_status
        )

        self.action_server = ActionServer(
            self,
            Transcribe,
            "/asr/transcribe",
            execute_callback=self._execute_transcribe,
            cancel_callback=self._reject_cancel,
        )
        self.audio_subscription = self.create_subscription(
            UInt8MultiArray, "/asr/audio_chunks", self._on_audio_chunk, 10
        )
        self.live_timer = self.create_timer(0.2, self._on_live_timer)

        self.get_logger().info(
            "ASR server started with "
            f"backend={self.backend_name}, live_stream_enabled={self.live_stream_enabled}, "
            f"sample_rate={self.sample_rate}"
        )

    def _backend_config(
        self,
        backend_name: str,
        *,
        model_override: str | None = None,
        region_override: str | None = None,
    ) -> dict[str, Any]:
        """Build final backend config with runtime model/region overrides."""
        cfg = dict(self.runtime_cfg.get("backends", {}).get(backend_name, {}))
        model_value = self.model if model_override is None else model_override
        region_value = self.region if region_override is None else region_override
        if model_value:
            cfg["model"] = model_value
        if region_value:
            cfg["region"] = region_value
        return cfg

    def _create_backend(
        self,
        backend_name: str,
        *,
        model_override: str | None = None,
        region_override: str | None = None,
    ):
        """Instantiate backend through core factory."""
        cfg = self._backend_config(
            backend_name,
            model_override=model_override,
            region_override=region_override,
        )
        return create_backend(backend_name, config=cfg)

    def _streaming_not_supported_response(
        self,
        *,
        language: str,
        error_code: str,
    ) -> AsrResponse:
        return AsrResponse(
            success=False,
            error_code=error_code,
            error_message=f"Backend '{self.backend_name}' does not support streaming",
            language=language,
            backend_info={
                "provider": self.backend_name,
                "model": self.model,
                "region": self.region,
            },
        )

    def _on_audio_chunk(self, msg: UInt8MultiArray) -> None:
        """Collect live audio chunks from `audio_capture_node`."""
        if not self.live_stream_enabled:
            return
        payload = bytes(msg.data)
        if not payload:
            return
        now_msg = self.get_clock().now().to_msg()
        with self._live_lock:
            if not self._live_chunks:
                self._live_capture_start = now_msg
            self._live_chunks.append(payload)
            self._live_last_chunk_ts = time.monotonic()
            self._live_capture_end = now_msg

    def _on_live_timer(self) -> None:
        """Flush buffered live chunks after inactivity timeout.

        This approximates phrase boundaries in "push-to-talk-free" mode.
        """
        if not self.live_stream_enabled:
            return
        chunks: list[bytes] = []
        capture_start: RosTime | None = None
        capture_end: RosTime | None = None
        with self._live_lock:
            if self._live_processing or not self._live_chunks:
                return
            if self._live_last_chunk_ts <= 0:
                return
            if (time.monotonic() - self._live_last_chunk_ts) < self.live_flush_timeout_sec:
                return
            chunks = list(self._live_chunks)
            capture_start = self._live_capture_start
            capture_end = self._live_capture_end
            self._live_chunks.clear()
            self._live_last_chunk_ts = 0.0
            self._live_capture_start = None
            self._live_capture_end = None
            self._live_processing = True

        try:
            with self.lock:
                if not bool(self.backend.capabilities.supports_streaming):
                    asr_response = self._streaming_not_supported_response(
                        language=self.language,
                        error_code="live_streaming_not_supported",
                    )
                else:
                    asr_response = self.backend.streaming_recognize(
                        chunks,
                        language=self.language,
                        sample_rate=self.sample_rate,
                    )
            rid = self._publish_response_and_metrics(
                asr_response,
                wav_path="live_input.wav",
                scenario="topic_streaming",
                capture_start=capture_start,
                capture_end=capture_end,
            )
            if asr_response.success:
                preview_text = asr_response.text[:120]
                compute_device = asr_response.backend_info.get("compute_device", "unknown")
                response_backend = asr_response.backend_info.get("provider", self.backend_name)
                self.get_logger().info(
                    "Live transcription published "
                    f"(backend={response_backend}, device={compute_device}, "
                    f"request_id={rid}, text='{preview_text}')"
                )
            else:
                err = f"{asr_response.error_code}: {asr_response.error_message}"
                self.get_logger().warning(f"Live transcription failed ({err})")
        except Exception as exc:
            self.get_logger().error(f"Live streaming processing failed: {exc}")
            error_response = AsrResponse(
                success=False,
                error_code="live_stream_error",
                error_message=str(exc),
                language=self.language,
                backend_info={
                    "provider": self.backend_name,
                    "model": self.model,
                    "region": self.region,
                },
            )
            self._publish_response_and_metrics(
                error_response,
                wav_path="live_input.wav",
                scenario="topic_streaming",
                capture_start=capture_start,
                capture_end=capture_end,
            )
        finally:
            with self._live_lock:
                self._live_processing = False

    def _publish_response_and_metrics(
        self,
        response: AsrResponse,
        *,
        wav_path: str,
        scenario: str,
        reference_text: str = "",
        request_id: str | None = None,
        capture_start: RosTime | None = None,
        capture_end: RosTime | None = None,
    ) -> str:
        """Publish text + metrics for any ASR response path."""
        rid = request_id or str(uuid.uuid4())
        result_msg = to_asr_result_msg(response, request_id=rid, is_final=True)
        self.text_pub.publish(result_msg)
        result_backend = str(response.backend_info.get("provider") or self.backend_name)
        compute_device = response.backend_info.get("compute_device", "")

        rec = self.collector.record(
            backend=result_backend,
            scenario=scenario,
            wav_path=wav_path,
            language=response.language or self.language,
            reference_text=reference_text,
            response=response,
            request_id=rid,
        )
        metrics_msg = build_metrics_msg(
            request_id=rid,
            backend=result_backend,
            wer=rec.wer,
            cer=rec.cer,
            rtf=rec.rtf,
            latency_ms=rec.latency_ms,
            cpu_percent=rec.cpu_percent,
            ram_mb=rec.ram_mb,
            gpu_util_percent=rec.gpu_util_percent,
            gpu_mem_mb=rec.gpu_mem_mb,
            cost_estimate=rec.cost_estimate,
            success=rec.success,
            capture_start=capture_start,
            capture_end=capture_end,
            text_preview=_preview_text(response.text),
            notes=f"scenario={scenario}" + (f",device={compute_device}" if compute_device else ""),
        )
        metrics_msg.header.stamp = self.get_clock().now().to_msg()
        self.metrics_pub.publish(metrics_msg)
        return rid

    def _on_recognize_once(self, request: RecognizeOnce.Request, response: RecognizeOnce.Response):
        """Handle `/asr/recognize_once` service."""
        wav_path = request.wav_path or self.runtime_cfg.get("asr", {}).get("wav_path", "")
        language = normalize_language_code(
            request.language or self.language,
            fallback=self.language,
        )
        if not wav_path or not Path(wav_path).exists():
            result = AsrResponse(
                success=False,
                error_code="file_missing",
                error_message=f"WAV file not found: {wav_path}",
                language=language,
                backend_info={
                    "provider": self.backend_name,
                    "model": self.model,
                    "region": self.region,
                },
            )
            rid = self._publish_response_and_metrics(
                result,
                wav_path=str(wav_path),
                scenario="service",
            )
            response.result = to_asr_result_msg(result, request_id=rid, is_final=True)
            return response

        req = AsrRequest(
            wav_path=wav_path,
            language=language,
            enable_word_timestamps=bool(request.enable_word_timestamps),
        )
        with self.lock:
            result = self.backend.recognize_once(req)
        rid = self._publish_response_and_metrics(result, wav_path=wav_path, scenario="service")
        response.result = to_asr_result_msg(result, request_id=rid, is_final=True)
        return response

    def _on_set_backend(self, request: SetAsrBackend.Request, response: SetAsrBackend.Response):
        """Handle runtime backend switch service."""
        requested_backend = str(request.backend or "").strip()
        if not requested_backend:
            response.success = False
            response.message = "Backend name must be non-empty"
            return response

        requested_model = str(request.model or self.model)
        requested_region = str(request.region or self.region)
        try:
            new_backend = self._create_backend(
                requested_backend,
                model_override=requested_model,
                region_override=requested_region,
            )
            with self.lock:
                self.backend_name = requested_backend
                self.model = requested_model
                self.region = requested_region
                self.backend = new_backend
            response.success = True
            response.message = f"Backend switched to {self.backend_name}"
            self.get_logger().info(response.message)
        except Exception as exc:
            response.success = False
            response.message = str(exc)
            self.get_logger().error(f"Failed to switch backend: {exc}")
        return response

    def _on_get_status(self, _: GetAsrStatus.Request, response: GetAsrStatus.Response):
        """Return backend capabilities and credential availability."""
        caps = self.backend.capabilities
        response.backend = self.backend_name
        response.model = self.model
        response.region = self.region
        response.capabilities = [
            f"recognize_once={caps.supports_recognize_once}",
            f"streaming={caps.supports_streaming}",
            f"streaming_mode={caps.streaming_mode}",
            f"word_timestamps={caps.supports_word_timestamps}",
            f"confidence={caps.supports_confidence}",
            f"is_cloud={caps.is_cloud}",
        ]
        response.streaming_supported = bool(caps.supports_streaming)
        response.cloud_credentials_available = bool(self.backend.has_credentials())
        response.status_message = "ok"
        return response

    def _reject_cancel(self, goal_handle) -> CancelResponse:
        self.get_logger().warning(
            f"Rejecting cancel request for transcribe goal {getattr(goal_handle, 'goal_id', '<unknown>')}"
        )
        return CancelResponse.REJECT

    async def _execute_transcribe(self, goal_handle):
        """Handle `/asr/transcribe` action.

        - `streaming=true`: emits periodic feedback and returns final result.
        - `streaming=false`: runs one-shot recognition.
        """
        goal = goal_handle.request
        wav_path = goal.wav_path
        language = normalize_language_code(goal.language or self.language, fallback=self.language)
        chunk_sec = goal.chunk_sec if goal.chunk_sec > 0 else self.chunk_sec

        if not wav_path or not Path(wav_path).exists():
            result = AsrResponse(
                success=False,
                error_code="file_missing",
                error_message=f"WAV file not found: {wav_path}",
                language=language,
                backend_info={
                    "provider": self.backend_name,
                    "model": self.model,
                    "region": self.region,
                },
            )
            goal_handle.abort()
            action_result = Transcribe.Result()
            action_result.result = to_asr_result_msg(result)
            return action_result

        try:
            if goal.streaming:
                chunks = wav_pcm_chunks(wav_path, chunk_sec)
                for idx in range(len(chunks)):
                    partial = AsrResponse(
                        text="",
                        partials=[f"chunk_{idx + 1}/{len(chunks)}"],
                        confidence=0.0,
                        language=language,
                        backend_info={
                            "provider": self.backend_name,
                            "model": self.model,
                            "region": self.region,
                        },
                    )
                    cpu, ram = collect_cpu_ram()
                    gpu_u, gpu_m = collect_gpu()
                    feedback = Transcribe.Feedback()
                    feedback.partial_result = to_asr_result_msg(partial, is_final=False)
                    feedback.metrics = build_metrics_msg(
                        request_id=str(uuid.uuid4()),
                        backend=self.backend_name,
                        wer=0.0,
                        cer=0.0,
                        rtf=0.0,
                        latency_ms=0.0,
                        cpu_percent=cpu,
                        ram_mb=ram,
                        gpu_util_percent=gpu_u,
                        gpu_mem_mb=gpu_m,
                        cost_estimate=0.0,
                        success=True,
                        notes="streaming_feedback",
                    )
                    feedback.metrics.header.stamp = self.get_clock().now().to_msg()
                    goal_handle.publish_feedback(feedback)
                with self.lock:
                    if not bool(self.backend.capabilities.supports_streaming):
                        asr_response = self._streaming_not_supported_response(
                            language=language,
                            error_code="action_streaming_not_supported",
                        )
                    else:
                        asr_response = self.backend.streaming_recognize(
                            chunks,
                            language=language,
                            sample_rate=self.sample_rate,
                        )
                scenario = "action_streaming"
            else:
                req = AsrRequest(wav_path=wav_path, language=language, enable_word_timestamps=True)
                with self.lock:
                    asr_response = self.backend.recognize_once(req)
                scenario = "action_once"
        except Exception as exc:
            asr_response = AsrResponse(
                success=False,
                error_code="action_runtime_error",
                error_message=str(exc),
                language=language,
                backend_info={
                    "provider": self.backend_name,
                    "model": self.model,
                    "region": self.region,
                },
            )
            scenario = "action_error"

        rid = self._publish_response_and_metrics(asr_response, wav_path=wav_path, scenario=scenario)
        goal_handle.succeed()
        action_result = Transcribe.Result()
        action_result.result = to_asr_result_msg(asr_response, request_id=rid)
        return action_result


def main() -> None:
    """Start the legacy all-in-one ASR server node."""
    rclpy.init()
    node = AsrServerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
