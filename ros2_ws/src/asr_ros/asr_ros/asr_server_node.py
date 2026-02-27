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
from asr_core.models import AsrRequest, AsrResponse
from asr_interfaces.action import Transcribe
from asr_interfaces.msg import AsrMetrics, AsrResult
from asr_interfaces.srv import GetAsrStatus, RecognizeOnce, SetAsrBackend
from asr_metrics.collector import MetricsCollector
from asr_metrics.system import collect_cpu_ram, collect_gpu
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import UInt8MultiArray

from asr_ros.converters import build_metrics_msg, to_asr_result_msg


class AsrServerNode(Node):
    def __init__(self) -> None:
        super().__init__("asr_server_node")
        self.declare_parameter("config", "configs/default.yaml")
        self.declare_parameter("backend", "")
        self.declare_parameter("language", "")
        self.declare_parameter("model", "")
        self.declare_parameter("region", "")
        self.declare_parameter("chunk_sec", 0.0)
        self.declare_parameter("sample_rate", 0)
        self.declare_parameter("live_stream_enabled", True)
        self.declare_parameter("live_flush_timeout_sec", 1.0)

        self.config_path = str(self.get_parameter("config").value)
        self.runtime_cfg = load_runtime_config(self.config_path, "configs/commercial.yaml")
        self.lock = threading.Lock()

        self.backend_name = str(
            self.get_parameter("backend").value
            or self.runtime_cfg.get("asr", {}).get("backend", "mock")
        )
        self.language = str(
            self.get_parameter("language").value
            or self.runtime_cfg.get("asr", {}).get("language", "en-US")
        )
        self.model = str(
            self.get_parameter("model").value or self.runtime_cfg.get("asr", {}).get("model", "")
        )
        self.region = str(
            self.get_parameter("region").value or self.runtime_cfg.get("asr", {}).get("region", "")
        )
        self.chunk_sec = float(
            self.get_parameter("chunk_sec").value
            or self.runtime_cfg.get("benchmark", {}).get("chunk_sec", 0.8)
        )
        self.sample_rate = int(
            self.get_parameter("sample_rate").value
            or self.runtime_cfg.get("asr", {}).get("sample_rate", 16000)
        )
        live_raw = self.get_parameter("live_stream_enabled").value
        if isinstance(live_raw, str):
            self.live_stream_enabled = live_raw.lower() in {"1", "true", "yes", "on"}
        else:
            self.live_stream_enabled = bool(live_raw)
        self.live_flush_timeout_sec = float(self.get_parameter("live_flush_timeout_sec").value)
        self._live_lock = threading.Lock()
        self._live_chunks: list[bytes] = []
        self._live_last_chunk_ts: float = 0.0
        self._live_processing = False

        self.collector = MetricsCollector(
            pricing_per_minute=self.runtime_cfg.get("benchmark", {}).get("pricing", {})
        )
        self.backend = self._create_backend(self.backend_name)

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

    def _backend_config(self, backend_name: str) -> dict[str, Any]:
        cfg = dict(self.runtime_cfg.get("backends", {}).get(backend_name, {}))
        if self.model:
            cfg["model"] = self.model
        if self.region:
            cfg["region"] = self.region
        return cfg

    def _create_backend(self, backend_name: str):
        cfg = self._backend_config(backend_name)
        return create_backend(backend_name, config=cfg)

    def _on_audio_chunk(self, msg: UInt8MultiArray) -> None:
        if not self.live_stream_enabled:
            return
        payload = bytes(msg.data)
        if not payload:
            return
        with self._live_lock:
            self._live_chunks.append(payload)
            self._live_last_chunk_ts = time.monotonic()

    def _on_live_timer(self) -> None:
        if not self.live_stream_enabled:
            return
        chunks: list[bytes] = []
        with self._live_lock:
            if self._live_processing or not self._live_chunks:
                return
            if self._live_last_chunk_ts <= 0:
                return
            if (time.monotonic() - self._live_last_chunk_ts) < self.live_flush_timeout_sec:
                return
            chunks = list(self._live_chunks)
            self._live_chunks.clear()
            self._live_last_chunk_ts = 0.0
            self._live_processing = True

        try:
            with self.lock:
                asr_response = self.backend.streaming_recognize(
                    chunks, language=self.language, sample_rate=self.sample_rate
                )
            rid = self._publish_response_and_metrics(
                asr_response,
                wav_path="live_input.wav",
                scenario="topic_streaming",
            )
            if asr_response.success:
                preview_text = asr_response.text[:120]
                compute_device = asr_response.backend_info.get("compute_device", "unknown")
                self.get_logger().info(
                    "Live transcription published "
                    f"(device={compute_device}, request_id={rid}, text='{preview_text}')"
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
    ) -> str:
        rid = request_id or str(uuid.uuid4())
        result_msg = to_asr_result_msg(response, request_id=rid, is_final=True)
        self.text_pub.publish(result_msg)
        compute_device = response.backend_info.get("compute_device", "")

        rec = self.collector.record(
            backend=self.backend_name,
            scenario=scenario,
            wav_path=wav_path,
            language=response.language or self.language,
            reference_text=reference_text,
            response=response,
            request_id=rid,
        )
        metrics_msg = build_metrics_msg(
            request_id=rid,
            backend=self.backend_name,
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
            notes=f"scenario={scenario}" + (f",device={compute_device}" if compute_device else ""),
        )
        self.metrics_pub.publish(metrics_msg)
        return rid

    def _on_recognize_once(self, request: RecognizeOnce.Request, response: RecognizeOnce.Response):
        wav_path = request.wav_path or self.runtime_cfg.get("asr", {}).get("wav_path", "")
        req = AsrRequest(
            wav_path=wav_path,
            language=request.language or self.language,
            enable_word_timestamps=bool(request.enable_word_timestamps),
        )
        with self.lock:
            result = self.backend.recognize_once(req)
        rid = self._publish_response_and_metrics(result, wav_path=wav_path, scenario="service")
        response.result = to_asr_result_msg(result, request_id=rid, is_final=True)
        return response

    def _on_set_backend(self, request: SetAsrBackend.Request, response: SetAsrBackend.Response):
        try:
            with self.lock:
                self.backend_name = request.backend
                self.model = request.model or self.model
                self.region = request.region or self.region
                self.backend = self._create_backend(self.backend_name)
            response.success = True
            response.message = f"Backend switched to {self.backend_name}"
            self.get_logger().info(response.message)
        except Exception as exc:
            response.success = False
            response.message = str(exc)
            self.get_logger().error(f"Failed to switch backend: {exc}")
        return response

    def _on_get_status(self, _: GetAsrStatus.Request, response: GetAsrStatus.Response):
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

    async def _execute_transcribe(self, goal_handle):
        goal = goal_handle.request
        wav_path = goal.wav_path
        language = goal.language or self.language
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

        with self.lock:
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
                    goal_handle.publish_feedback(feedback)
                asr_response = self.backend.streaming_recognize(
                    chunks,
                    language=language,
                    sample_rate=self.sample_rate,
                )
                scenario = "action_streaming"
            else:
                req = AsrRequest(wav_path=wav_path, language=language, enable_word_timestamps=True)
                asr_response = self.backend.recognize_once(req)
                scenario = "action_once"

        rid = self._publish_response_and_metrics(asr_response, wav_path=wav_path, scenario=scenario)
        goal_handle.succeed()
        action_result = Transcribe.Result()
        action_result.result = to_asr_result_msg(asr_response, request_id=rid)
        return action_result


def main() -> None:
    rclpy.init()
    node = AsrServerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
