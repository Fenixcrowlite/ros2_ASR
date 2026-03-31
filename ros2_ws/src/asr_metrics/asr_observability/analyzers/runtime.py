"""Trace analyzers for runtime and benchmark executions."""

from __future__ import annotations

from typing import Any

from asr_metrics.quality import has_quality_reference, text_quality_support
from asr_metrics.system import collect_cpu_ram, collect_gpu

from asr_observability.collectors.pipeline import PipelineTraceCollector
from asr_observability.config import ObservabilityConfig
from asr_observability.models import PipelineTrace
from asr_observability.validators.runtime import validate_trace


def _trace_stage_duration(trace: PipelineTrace, stage_name: str) -> float:
    for stage in trace.stages:
        if stage.stage == stage_name:
            return float(stage.duration_ms)
    return 0.0


def _set_latency_metrics(
    collector: PipelineTraceCollector,
    *,
    audio_load_ms: float,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    total_latency_ms: float,
    ros_service_latency_ms: float,
    time_to_result_ms: float,
    audio_duration_sec: float,
) -> None:
    collector.set_metric("audio_load_ms", audio_load_ms)
    collector.set_metric("preprocess_ms", preprocess_ms)
    collector.set_metric("inference_ms", inference_ms)
    collector.set_metric("postprocess_ms", postprocess_ms)
    collector.set_metric("total_latency_ms", total_latency_ms)
    collector.set_metric("ros_service_latency_ms", ros_service_latency_ms)
    collector.set_metric("time_to_result_ms", time_to_result_ms)
    collector.set_metric("audio_duration_sec", audio_duration_sec)
    collector.set_metric(
        "real_time_factor",
        (total_latency_ms / 1000.0) / audio_duration_sec if audio_duration_sec > 0 else 0.0,
    )


def _attach_system_metrics(collector: PipelineTraceCollector, config: ObservabilityConfig) -> None:
    if not config.include_system_metrics:
        return
    cpu_percent, ram_mb = collect_cpu_ram()
    collector.set_metric("cpu_percent", cpu_percent)
    collector.set_metric("memory_mb", ram_mb)
    if config.include_gpu_metrics:
        gpu_util_percent, gpu_mem_mb = collect_gpu()
        collector.set_metric("gpu_util_percent", gpu_util_percent)
        collector.set_metric("gpu_memory_mb", gpu_mem_mb)


def build_runtime_trace(
    *,
    collector: PipelineTraceCollector,
    config: ObservabilityConfig,
    provider_id: str,
    text: str,
    confidence: float,
    success: bool,
    degraded: bool,
    error_code: str,
    error_message: str,
    language: str,
    audio_duration_sec: float,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    total_latency_ms: float,
    ros_service_latency_ms: float = 0.0,
    reference_text: str = "",
    extra_metrics: dict[str, Any] | None = None,
) -> PipelineTrace:
    collector.update_metadata(
        provider_id=provider_id,
        text=text,
        language=language,
        success=success,
        degraded=degraded,
        error_code=error_code,
    )
    collector.set_metric("confidence", confidence)
    collector.set_metric("success", success)
    collector.set_metric("degraded", degraded)
    collector.set_metric("error_code", error_code)
    collector.set_metric("error_message", error_message)
    _set_latency_metrics(
        collector,
        audio_load_ms=_trace_stage_duration(collector.trace, "audio_load"),
        preprocess_ms=preprocess_ms,
        inference_ms=inference_ms,
        postprocess_ms=postprocess_ms,
        total_latency_ms=total_latency_ms,
        ros_service_latency_ms=ros_service_latency_ms,
        time_to_result_ms=max(ros_service_latency_ms, collector.finalize().total_duration_ms),
        audio_duration_sec=audio_duration_sec,
    )
    if reference_text and has_quality_reference(reference_text):
        support = text_quality_support(reference_text, text)
        collector.set_metric("wer", support.wer)
        collector.set_metric("cer", support.cer)
    if extra_metrics:
        for key, value in extra_metrics.items():
            collector.set_metric(key, value)
    _attach_system_metrics(collector, config)
    trace = collector.trace
    trace.validation = validate_trace(
        trace, require_ordered_timestamps=config.require_ordered_timestamps
    )
    return trace


def build_benchmark_trace(
    *,
    collector: PipelineTraceCollector,
    config: ObservabilityConfig,
    provider_id: str,
    text: str,
    confidence: float,
    success: bool,
    degraded: bool,
    error_code: str,
    error_message: str,
    language: str,
    audio_duration_sec: float,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    total_latency_ms: float,
    reference_text: str,
    extra_metrics: dict[str, Any] | None = None,
) -> PipelineTrace:
    collector.update_metadata(
        provider_id=provider_id,
        language=language,
        success=success,
        degraded=degraded,
        error_code=error_code,
    )
    collector.set_metric("confidence", confidence)
    collector.set_metric("success", success)
    collector.set_metric("degraded", degraded)
    collector.set_metric("error_code", error_code)
    collector.set_metric("error_message", error_message)
    _set_latency_metrics(
        collector,
        audio_load_ms=_trace_stage_duration(collector.trace, "audio_load"),
        preprocess_ms=preprocess_ms,
        inference_ms=inference_ms,
        postprocess_ms=postprocess_ms,
        total_latency_ms=total_latency_ms,
        ros_service_latency_ms=0.0,
        time_to_result_ms=collector.finalize().total_duration_ms,
        audio_duration_sec=audio_duration_sec,
    )
    if has_quality_reference(reference_text):
        support = text_quality_support(reference_text, text)
        collector.set_metric("wer", support.wer)
        collector.set_metric("cer", support.cer)
        collector.set_metric("reference_word_count", support.reference_word_count)
        collector.set_metric("reference_char_count", support.reference_char_count)
        collector.set_metric("word_edits", support.word_edits)
        collector.set_metric("char_edits", support.char_edits)
    if extra_metrics:
        for key, value in extra_metrics.items():
            collector.set_metric(key, value)
    _attach_system_metrics(collector, config)
    trace = collector.trace
    trace.validation = validate_trace(
        trace, require_ordered_timestamps=config.require_ordered_timestamps
    )
    return trace
