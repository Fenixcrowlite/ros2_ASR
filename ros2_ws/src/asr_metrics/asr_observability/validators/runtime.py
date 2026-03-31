"""Validation rules for trace payloads and derived metrics."""

from __future__ import annotations

from asr_observability.models import PipelineTrace, ValidationReport


def validate_trace(
    trace: PipelineTrace,
    *,
    require_ordered_timestamps: bool = True,
) -> ValidationReport:
    report = ValidationReport()
    ordered_cursor = trace.started_ns
    for stage in trace.stages:
        if stage.duration_ms < 0:
            report.errors.append(f"Negative latency for stage `{stage.stage}`")
        if require_ordered_timestamps and stage.started_ns < ordered_cursor:
            report.errors.append(f"Out-of-order timestamp at stage `{stage.stage}`")
        if stage.ended_ns < stage.started_ns:
            report.errors.append(f"Stage `{stage.stage}` ended before it started")
        ordered_cursor = stage.ended_ns

    metric_values = trace.metrics
    for key in (
        "audio_load_ms",
        "preprocess_ms",
        "inference_ms",
        "postprocess_ms",
        "total_latency_ms",
        "ros_service_latency_ms",
        "time_to_result_ms",
        "real_time_factor",
    ):
        value = metric_values.get(key)
        if value is None:
            report.errors.append(f"Missing metric `{key}`")
            continue
        if float(value) < 0.0:
            report.errors.append(f"Metric `{key}` must be >= 0")

    for key in ("wer", "cer"):
        value = metric_values.get(key)
        if value is None:
            continue
        numeric_value = float(value)
        if numeric_value < 0.0:
            report.errors.append(f"Metric `{key}` must be >= 0")

    confidence = metric_values.get("confidence")
    if confidence is not None:
        numeric_confidence = float(confidence)
        if numeric_confidence < 0.0 or numeric_confidence > 1.0:
            report.warnings.append("confidence is outside 0..1")

    report.valid = not report.errors
    report.corrupted = bool(report.errors)
    return report
