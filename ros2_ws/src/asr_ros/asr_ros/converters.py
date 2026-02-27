"""Converters between core dataclasses and ROS2 message types."""

from __future__ import annotations

import uuid

from asr_core.models import AsrResponse
from asr_interfaces.msg import AsrMetrics, AsrResult, WordTimestamp


def to_asr_result_msg(
    response: AsrResponse, request_id: str | None = None, is_final: bool = True
) -> AsrResult:
    """Map `AsrResponse` -> `asr_interfaces/msg/AsrResult`."""
    msg = AsrResult()
    msg.request_id = request_id or str(uuid.uuid4())
    msg.text = response.text
    msg.partials = list(response.partials)
    msg.confidence = float(response.confidence)
    msg.word_timestamps = [
        WordTimestamp(
            word=w.word,
            start_sec=float(w.start_sec),
            end_sec=float(w.end_sec),
            confidence=float(w.confidence),
        )
        for w in response.word_timestamps
    ]
    msg.language = response.language
    msg.backend = response.backend_info.get("provider", "")
    msg.model = response.backend_info.get("model", "")
    msg.region = response.backend_info.get("region", "")
    msg.audio_duration_sec = float(response.audio_duration_sec)
    msg.preprocess_ms = float(response.timings.preprocess_ms)
    msg.inference_ms = float(response.timings.inference_ms)
    msg.postprocess_ms = float(response.timings.postprocess_ms)
    msg.total_ms = float(response.timings.total_ms)
    msg.is_final = bool(is_final)
    msg.success = bool(response.success)
    msg.error_code = response.error_code
    msg.error_message = response.error_message
    return msg


def build_metrics_msg(
    *,
    request_id: str,
    backend: str,
    wer: float,
    cer: float,
    rtf: float,
    latency_ms: float,
    cpu_percent: float,
    ram_mb: float,
    gpu_util_percent: float,
    gpu_mem_mb: float,
    cost_estimate: float,
    success: bool,
    notes: str,
) -> AsrMetrics:
    """Build `AsrMetrics` ROS message from collected benchmark/telemetry values."""
    msg = AsrMetrics()
    msg.request_id = request_id
    msg.backend = backend
    msg.wer = float(wer)
    msg.cer = float(cer)
    msg.rtf = float(rtf)
    msg.latency_ms = float(latency_ms)
    msg.cpu_percent = float(cpu_percent)
    msg.ram_mb = float(ram_mb)
    msg.gpu_util_percent = float(gpu_util_percent)
    msg.gpu_mem_mb = float(gpu_mem_mb)
    msg.cost_estimate = float(cost_estimate)
    msg.success = bool(success)
    msg.notes = notes
    return msg
