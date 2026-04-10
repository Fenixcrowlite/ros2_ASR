"""Trace analyzers for runtime and benchmark executions."""

from __future__ import annotations

from typing import Any

from asr_metrics.quality import has_quality_reference, text_quality_support
from asr_metrics.semantics import (
    METRICS_SEMANTICS_VERSION,
    apply_legacy_metric_aliases,
    resolve_audio_duration_fields,
)
from asr_metrics.system import ResourceSampleSummary, collect_cpu_ram, collect_gpu

from asr_observability.collectors.pipeline import PipelineTraceCollector
from asr_observability.config import ObservabilityConfig
from asr_observability.models import PipelineTrace
from asr_observability.validators.runtime import validate_trace


def _trace_stage_duration(trace: PipelineTrace, stage_name: str) -> float:
    for stage in trace.stages:
        if stage.stage == stage_name:
            return float(stage.duration_ms)
    return 0.0


def _set_trace_metrics(
    collector: PipelineTraceCollector,
    *,
    audio_load_ms: float,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    provider_compute_latency_ms: float,
    end_to_end_latency_ms: float,
    time_to_first_result_ms: float,
    time_to_final_result_ms: float,
    finalization_latency_ms: float | None,
    ros_service_latency_ms: float,
    measured_audio_duration_sec: float | None,
    declared_audio_duration_sec: float | None,
    audio_duration_source: str,
) -> None:
    collector.set_metric("audio_load_ms", audio_load_ms)
    collector.set_metric("preprocess_ms", preprocess_ms)
    collector.set_metric("inference_ms", inference_ms)
    collector.set_metric("postprocess_ms", postprocess_ms)
    collector.set_metric("provider_compute_latency_ms", provider_compute_latency_ms)
    collector.set_metric("end_to_end_latency_ms", end_to_end_latency_ms)
    collector.set_metric("ros_service_latency_ms", ros_service_latency_ms)
    collector.set_metric("time_to_first_result_ms", time_to_first_result_ms)
    collector.set_metric("time_to_final_result_ms", time_to_final_result_ms)
    if finalization_latency_ms is not None:
        collector.set_metric("finalization_latency_ms", finalization_latency_ms)
    duration_fields = resolve_audio_duration_fields(
        measured_audio_duration_sec=measured_audio_duration_sec,
        declared_audio_duration_sec=declared_audio_duration_sec,
    )
    duration_fields["audio_duration_source"] = str(
        audio_duration_source or duration_fields["audio_duration_source"]
    )
    for key, value in duration_fields.items():
        collector.set_metric(key, value)


def _attach_resource_metrics(
    collector: PipelineTraceCollector,
    config: ObservabilityConfig,
    resource_sample: ResourceSampleSummary | None,
) -> None:
    if not config.include_system_metrics:
        return
    if resource_sample is None:
        cpu_percent, ram_mb = collect_cpu_ram()
        collector.set_metric("cpu_percent_mean", cpu_percent)
        collector.set_metric("cpu_percent_peak", cpu_percent)
        collector.set_metric("memory_mb_mean", ram_mb)
        collector.set_metric("memory_mb_peak", ram_mb)
        if config.include_gpu_metrics:
            gpu_util_percent, gpu_mem_mb = collect_gpu()
            collector.set_metric("gpu_util_percent_mean", gpu_util_percent)
            collector.set_metric("gpu_util_percent_peak", gpu_util_percent)
            collector.set_metric("gpu_memory_mb_mean", gpu_mem_mb)
            collector.set_metric("gpu_memory_mb_peak", gpu_mem_mb)
        return

    for key, value in resource_sample.as_metrics().items():
        if not config.include_gpu_metrics and key.startswith("gpu_"):
            continue
        collector.set_metric(key, value)


def _finalize_trace(
    collector: PipelineTraceCollector,
    *,
    config: ObservabilityConfig,
) -> PipelineTrace:
    trace = collector.finalize()
    apply_legacy_metric_aliases(trace.metrics)
    trace.metrics_semantics_version = METRICS_SEMANTICS_VERSION
    trace.legacy_metrics = False
    trace.validation = validate_trace(
        trace, require_ordered_timestamps=config.require_ordered_timestamps
    )
    return trace


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
    measured_audio_duration_sec: float | None,
    declared_audio_duration_sec: float | None,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    provider_compute_latency_ms: float,
    end_to_end_latency_ms: float,
    time_to_first_result_ms: float,
    time_to_final_result_ms: float,
    finalization_latency_ms: float | None = None,
    ros_service_latency_ms: float = 0.0,
    resource_sample: ResourceSampleSummary | None = None,
    audio_duration_source: str = "manifest_declared",
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
    _set_trace_metrics(
        collector,
        audio_load_ms=_trace_stage_duration(collector.trace, "audio_load"),
        preprocess_ms=preprocess_ms,
        inference_ms=inference_ms,
        postprocess_ms=postprocess_ms,
        provider_compute_latency_ms=provider_compute_latency_ms,
        end_to_end_latency_ms=end_to_end_latency_ms,
        time_to_first_result_ms=time_to_first_result_ms,
        time_to_final_result_ms=time_to_final_result_ms,
        finalization_latency_ms=finalization_latency_ms,
        ros_service_latency_ms=ros_service_latency_ms,
        measured_audio_duration_sec=measured_audio_duration_sec,
        declared_audio_duration_sec=declared_audio_duration_sec,
        audio_duration_source=audio_duration_source,
    )
    if reference_text and has_quality_reference(reference_text):
        support = text_quality_support(reference_text, text)
        collector.set_metric("wer", support.wer)
        collector.set_metric("cer", support.cer)
    if extra_metrics:
        for key, value in extra_metrics.items():
            collector.set_metric(key, value)
    _attach_resource_metrics(collector, config, resource_sample)
    return _finalize_trace(collector, config=config)


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
    measured_audio_duration_sec: float | None,
    declared_audio_duration_sec: float | None,
    preprocess_ms: float,
    inference_ms: float,
    postprocess_ms: float,
    provider_compute_latency_ms: float,
    end_to_end_latency_ms: float,
    time_to_first_result_ms: float,
    time_to_final_result_ms: float,
    finalization_latency_ms: float | None = None,
    resource_sample: ResourceSampleSummary | None = None,
    audio_duration_source: str = "manifest_declared",
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
    _set_trace_metrics(
        collector,
        audio_load_ms=_trace_stage_duration(collector.trace, "audio_load"),
        preprocess_ms=preprocess_ms,
        inference_ms=inference_ms,
        postprocess_ms=postprocess_ms,
        provider_compute_latency_ms=provider_compute_latency_ms,
        end_to_end_latency_ms=end_to_end_latency_ms,
        time_to_first_result_ms=time_to_first_result_ms,
        time_to_final_result_ms=time_to_final_result_ms,
        finalization_latency_ms=finalization_latency_ms,
        ros_service_latency_ms=0.0,
        measured_audio_duration_sec=measured_audio_duration_sec,
        declared_audio_duration_sec=declared_audio_duration_sec,
        audio_duration_source=audio_duration_source,
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
    _attach_resource_metrics(collector, config, resource_sample)
    return _finalize_trace(collector, config=config)
