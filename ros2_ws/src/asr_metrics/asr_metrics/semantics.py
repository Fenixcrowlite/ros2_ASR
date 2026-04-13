"""Canonical timing/resource semantics shared across benchmark and runtime flows."""

from __future__ import annotations

from typing import Any

METRICS_SEMANTICS_VERSION = 2

CANONICAL_LATENCY_METRICS = (
    "provider_compute_latency_ms",
    "end_to_end_latency_ms",
    "time_to_first_result_ms",
    "time_to_final_result_ms",
    "finalization_latency_ms",
)

CANONICAL_DURATION_METRICS = (
    "measured_audio_duration_sec",
    "declared_audio_duration_sec",
    "duration_mismatch_sec",
    "audio_duration_source",
)

CANONICAL_RTF_METRICS = (
    "provider_compute_rtf",
    "end_to_end_rtf",
)

CANONICAL_RESOURCE_METRICS = (
    "cpu_percent_mean",
    "cpu_percent_peak",
    "memory_mb_mean",
    "memory_mb_peak",
    "gpu_util_percent_mean",
    "gpu_util_percent_peak",
    "gpu_memory_mb_mean",
    "gpu_memory_mb_peak",
)

LEGACY_ALIAS_MAP: dict[str, str] = {
    "total_latency_ms": "provider_compute_latency_ms",
    "per_utterance_latency_ms": "provider_compute_latency_ms",
    "real_time_factor": "provider_compute_rtf",
    "time_to_result_ms": "time_to_final_result_ms",
    "cpu_percent": "cpu_percent_mean",
    "memory_mb": "memory_mb_mean",
    "gpu_util_percent": "gpu_util_percent_mean",
    "gpu_memory_mb": "gpu_memory_mb_mean",
}

OPTIONAL_CANONICAL_METRICS = {
    "finalization_latency_ms",
    "gpu_util_percent_mean",
    "gpu_util_percent_peak",
    "gpu_memory_mb_mean",
    "gpu_memory_mb_peak",
}


def float_or_none(value: Any) -> float | None:
    """Best-effort float conversion that treats empty values as missing."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    """Best-effort int conversion that treats empty values as missing."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def duration_mismatch_threshold_sec(measured: float, declared: float) -> float:
    """Return the tolerance used when comparing measured vs declared duration."""
    return max(0.05, 0.02 * max(abs(float(measured)), abs(float(declared))))


def duration_mismatch_sec(measured: float | None, declared: float | None) -> float:
    """Return the absolute duration difference, or zero when one side is missing."""
    if measured is None or declared is None:
        return 0.0
    return abs(float(measured) - float(declared))


def duration_mismatch_is_suspicious(measured: float | None, declared: float | None) -> bool:
    """Return whether the duration mismatch exceeds the allowed tolerance."""
    if measured is None or declared is None:
        return False
    mismatch = duration_mismatch_sec(measured, declared)
    return mismatch > duration_mismatch_threshold_sec(float(measured), float(declared))


def resolve_audio_duration_fields(
    *,
    measured_audio_duration_sec: float | None,
    declared_audio_duration_sec: float | None,
) -> dict[str, Any]:
    """Build canonical audio-duration fields shared by runtime and benchmark metrics."""
    measured = float_or_none(measured_audio_duration_sec)
    declared = float_or_none(declared_audio_duration_sec)
    source = "manifest_declared"
    effective = declared if declared is not None else 0.0
    if measured is not None and measured > 0.0:
        source = "measured_file"
        effective = measured
    return {
        "audio_duration_sec": float(effective or 0.0),
        "measured_audio_duration_sec": measured,
        "declared_audio_duration_sec": declared,
        "duration_mismatch_sec": duration_mismatch_sec(measured, declared),
        "audio_duration_source": source,
    }


def ensure_canonical_rtfs(metrics: dict[str, Any]) -> None:
    """Backfill canonical real-time-factor metrics from latency and duration values."""
    measured_duration = float_or_none(metrics.get("measured_audio_duration_sec"))
    if measured_duration is None or measured_duration <= 0.0:
        measured_duration = float_or_none(metrics.get("audio_duration_sec"))
    if measured_duration is None or measured_duration <= 0.0:
        metrics.setdefault("provider_compute_rtf", 0.0)
        metrics.setdefault("end_to_end_rtf", 0.0)
        return
    provider_latency = float_or_none(metrics.get("provider_compute_latency_ms")) or 0.0
    end_to_end_latency = float_or_none(metrics.get("end_to_end_latency_ms")) or 0.0
    metrics["provider_compute_rtf"] = (provider_latency / 1000.0) / measured_duration
    metrics["end_to_end_rtf"] = (end_to_end_latency / 1000.0) / measured_duration


def apply_legacy_metric_aliases(metrics: dict[str, Any]) -> dict[str, Any]:
    """Populate deprecated metric aliases so old readers still see expected keys."""
    ensure_canonical_rtfs(metrics)
    for legacy_name, canonical_name in LEGACY_ALIAS_MAP.items():
        if metrics.get(legacy_name) in (None, "") and metrics.get(canonical_name) not in (None, ""):
            metrics[legacy_name] = metrics.get(canonical_name)
    return metrics


def alias_tolerance(canonical_value: Any) -> float:
    """Return the tolerance used when comparing canonical and alias metric values."""
    numeric = abs(float(float_or_none(canonical_value) or 0.0))
    return max(2.0, numeric * 0.02)


def metric_semantics_version(payload: Any) -> int:
    """Extract the metrics semantics version from a dict or object payload."""
    if isinstance(payload, dict):
        version = int_or_none(payload.get("metrics_semantics_version"))
        if version is not None:
            return version
    version = int_or_none(getattr(payload, "metrics_semantics_version", None))
    if version is not None:
        return version
    return 1


def is_legacy_metrics_payload(payload: Any) -> bool:
    """Return whether a payload should be interpreted with legacy metric semantics."""
    if isinstance(payload, dict) and "legacy_metrics" in payload:
        return bool(payload.get("legacy_metrics"))
    legacy = getattr(payload, "legacy_metrics", None)
    if legacy is not None:
        return bool(legacy)
    return metric_semantics_version(payload) < METRICS_SEMANTICS_VERSION
