"""Validation rules for trace payloads and derived metrics."""

from __future__ import annotations

from asr_metrics.semantics import (
    METRICS_SEMANTICS_VERSION,
    OPTIONAL_CANONICAL_METRICS,
    duration_mismatch_is_suspicious,
    float_or_none,
    metric_semantics_version,
)

from asr_observability.models import PipelineTrace, ValidationReport


def _validate_stage_order(
    trace: PipelineTrace,
    report: ValidationReport,
    *,
    require_ordered_timestamps: bool,
) -> None:
    ordered_cursor = trace.started_ns
    for stage in trace.stages:
        if stage.duration_ms < 0:
            report.errors.append(f"Negative latency for stage `{stage.stage}`")
        if require_ordered_timestamps and stage.started_ns < ordered_cursor:
            report.errors.append(f"Out-of-order timestamp at stage `{stage.stage}`")
        if stage.ended_ns < stage.started_ns:
            report.errors.append(f"Stage `{stage.stage}` ended before it started")
        ordered_cursor = stage.ended_ns


def _require_non_negative(
    metric_values: dict[str, object],
    report: ValidationReport,
    names: tuple[str, ...],
) -> None:
    for key in names:
        value = metric_values.get(key)
        numeric = float_or_none(value)
        if value is None:
            report.errors.append(f"Missing metric `{key}`")
            continue
        if numeric is None:
            report.errors.append(f"Metric `{key}` must be numeric")
            continue
        if numeric < 0.0:
            report.errors.append(f"Metric `{key}` must be >= 0")


def _validate_canonical_trace(metric_values: dict[str, object], report: ValidationReport) -> None:
    _require_non_negative(
        metric_values,
        report,
        (
            "audio_load_ms",
            "preprocess_ms",
            "inference_ms",
            "postprocess_ms",
            "provider_compute_latency_ms",
            "end_to_end_latency_ms",
            "time_to_first_result_ms",
            "time_to_final_result_ms",
            "provider_compute_rtf",
            "end_to_end_rtf",
        ),
    )

    for key in (
        "finalization_latency_ms",
        "cpu_percent_mean",
        "cpu_percent_peak",
        "memory_mb_mean",
        "memory_mb_peak",
        "gpu_util_percent_mean",
        "gpu_util_percent_peak",
        "gpu_memory_mb_mean",
        "gpu_memory_mb_peak",
    ):
        numeric = float_or_none(metric_values.get(key))
        if numeric is None:
            if key in OPTIONAL_CANONICAL_METRICS:
                report.warnings.append(f"Optional metric `{key}` unavailable")
            continue
        if numeric < 0.0:
            report.errors.append(f"Metric `{key}` must be >= 0")

    provider_latency = float_or_none(metric_values.get("provider_compute_latency_ms"))
    end_to_end_latency = float_or_none(metric_values.get("end_to_end_latency_ms"))
    time_to_first = float_or_none(metric_values.get("time_to_first_result_ms"))
    time_to_final = float_or_none(metric_values.get("time_to_final_result_ms"))
    if (
        provider_latency is not None
        and end_to_end_latency is not None
        and provider_latency > end_to_end_latency + 5.0
    ):
        report.errors.append(
            "Metric `provider_compute_latency_ms` must be <= `end_to_end_latency_ms` + 5 ms"
        )
    if (
        time_to_first is not None
        and time_to_final is not None
        and time_to_first > time_to_final + 2.0
    ):
        report.errors.append(
            "Metric `time_to_first_result_ms` must be <= `time_to_final_result_ms` + 2 ms"
        )

    measured = float_or_none(metric_values.get("measured_audio_duration_sec"))
    declared = float_or_none(metric_values.get("declared_audio_duration_sec"))
    if duration_mismatch_is_suspicious(measured, declared):
        report.warnings.append("Measured and declared audio durations differ materially")


def validate_trace(
    trace: PipelineTrace,
    *,
    require_ordered_timestamps: bool = True,
) -> ValidationReport:
    """Validate an exported trace for structural and semantic consistency."""
    report = ValidationReport()
    _validate_stage_order(
        trace,
        report,
        require_ordered_timestamps=require_ordered_timestamps,
    )

    metric_values = trace.metrics
    semantics_version = metric_semantics_version(trace)
    if semantics_version < METRICS_SEMANTICS_VERSION:
        report.errors.append("Trace metrics semantics version is unsupported")
    _validate_canonical_trace(metric_values, report)

    for key in ("wer", "cer"):
        numeric_value = float_or_none(metric_values.get(key))
        if numeric_value is None:
            continue
        if numeric_value < 0.0:
            report.errors.append(f"Metric `{key}` must be >= 0")

    confidence = metric_values.get("confidence")
    numeric_confidence = float_or_none(confidence)
    if numeric_confidence is not None and (numeric_confidence < 0.0 or numeric_confidence > 1.0):
        report.warnings.append("confidence is outside 0..1")

    report.valid = not report.errors
    report.corrupted = bool(report.errors)
    return report
