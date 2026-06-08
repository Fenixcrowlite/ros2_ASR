"""Metric registry with semantics used by benchmarks, reports, and UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Describes one metric exposed by the benchmark/runtime reporting layer."""

    name: str
    display_name: str
    unit: str
    category: str
    preferred_direction: str
    description: str
    summary_aggregator: str = "mean"
    applicable_execution_modes: tuple[str, ...] = ("batch", "streaming")
    summary_weight_metric: str = ""
    deprecated: bool = False
    alias_of: str = ""

    def as_dict(self) -> dict[str, object]:
        """Serialize the metric definition for APIs, reports, and UI metadata."""
        return asdict(self)


def _metric(
    name: str,
    display_name: str,
    unit: str,
    category: str,
    preferred_direction: str,
    description: str,
    *,
    summary_aggregator: str = "mean",
    applicable_execution_modes: tuple[str, ...] = ("batch", "streaming"),
    summary_weight_metric: str = "",
    deprecated: bool = False,
    alias_of: str = "",
) -> MetricDefinition:
    return MetricDefinition(
        name=name,
        display_name=display_name,
        unit=unit,
        category=category,
        preferred_direction=preferred_direction,
        description=description,
        summary_aggregator=summary_aggregator,
        applicable_execution_modes=applicable_execution_modes,
        summary_weight_metric=summary_weight_metric,
        deprecated=deprecated,
        alias_of=alias_of,
    )


METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "wer": _metric(
        "wer",
        "WER",
        "ratio",
        "quality",
        "lower",
        "Corpus-level word error rate against the normalized reference transcript.",
        summary_aggregator="corpus_rate",
    ),
    "cer": _metric(
        "cer",
        "CER",
        "ratio",
        "quality",
        "lower",
        "Corpus-level character error rate after normalization and whitespace removal.",
        summary_aggregator="corpus_rate",
    ),
    "sample_accuracy": _metric(
        "sample_accuracy",
        "Exact Match Rate",
        "ratio",
        "quality",
        "higher",
        "Share of samples whose normalized reference and hypothesis match exactly.",
        summary_aggregator="rate",
    ),
    "ser": _metric(
        "ser",
        "SER",
        "ratio",
        "quality",
        "lower",
        "Sentence error rate derived as 1 - sample_accuracy.",
        summary_aggregator="rate",
    ),
    "mer": _metric(
        "mer",
        "MER",
        "ratio",
        "quality",
        "lower",
        "Match error rate: (S + D + I) / (H + S + D + I) from word alignment counts.",
        summary_aggregator="alignment_rate",
    ),
    "wil": _metric(
        "wil",
        "WIL",
        "ratio",
        "quality",
        "lower",
        "Word information lost, computed as 1 - WIP from word alignment counts.",
        summary_aggregator="alignment_rate",
    ),
    "wip": _metric(
        "wip",
        "WIP",
        "ratio",
        "quality",
        "higher",
        "Word information preserved from word-level precision and recall.",
        summary_aggregator="alignment_rate",
    ),
    "micro_wer": _metric(
        "micro_wer",
        "Micro WER",
        "ratio",
        "quality",
        "lower",
        "Word error rate computed from summed word edits and summed reference words.",
        summary_aggregator="corpus_rate",
    ),
    "macro_wer": _metric(
        "macro_wer",
        "Macro WER",
        "ratio",
        "quality",
        "lower",
        "Mean of per-sample WER values with defined non-empty references.",
        summary_aggregator="macro_mean",
    ),
    "micro_cer": _metric(
        "micro_cer",
        "Micro CER",
        "ratio",
        "quality",
        "lower",
        "Character error rate computed from summed character edits and summed reference characters.",
        summary_aggregator="corpus_rate",
    ),
    "macro_cer": _metric(
        "macro_cer",
        "Macro CER",
        "ratio",
        "quality",
        "lower",
        "Mean of per-sample CER values with defined non-empty references.",
        summary_aggregator="macro_mean",
    ),
    "hallucination_on_silence": _metric(
        "hallucination_on_silence",
        "Hallucination On Silence",
        "ratio",
        "quality",
        "lower",
        "Share of empty-reference samples that produced a non-empty normalized hypothesis.",
        summary_aggregator="rate",
    ),
    "provider_compute_latency_ms": _metric(
        "provider_compute_latency_ms",
        "Provider Compute Latency",
        "ms",
        "latency",
        "lower",
        "Provider-reported compute latency from normalized ASR result timings.",
    ),
    "end_to_end_latency_ms": _metric(
        "end_to_end_latency_ms",
        "End-To-End Latency",
        "ms",
        "latency",
        "lower",
        "Outer wall-clock latency from request/segment/stream start to final result availability.",
    ),
    "time_to_first_result_ms": _metric(
        "time_to_first_result_ms",
        "Time To First Result",
        "ms",
        "latency",
        "lower",
        (
            "Wall-clock latency from request/stream start to the first visible "
            "partial or final result."
        ),
    ),
    "time_to_final_result_ms": _metric(
        "time_to_final_result_ms",
        "Time To Final Result",
        "ms",
        "latency",
        "lower",
        "Wall-clock latency from request/stream start to the final result.",
    ),
    "provider_compute_rtf": _metric(
        "provider_compute_rtf",
        "Provider Compute RTF",
        "ratio",
        "latency",
        "lower",
        "Provider compute latency divided by measured audio duration.",
    ),
    "end_to_end_rtf": _metric(
        "end_to_end_rtf",
        "End-To-End RTF",
        "ratio",
        "latency",
        "lower",
        "Wall-clock end-to-end latency divided by measured audio duration.",
    ),
    "confidence": _metric(
        "confidence",
        "Confidence",
        "ratio",
        "quality",
        "higher",
        "Average confidence exposed by the provider for the recognized utterance.",
    ),
    "audio_load_ms": _metric(
        "audio_load_ms",
        "Audio Load",
        "ms",
        "latency",
        "lower",
        "Time spent loading or materializing input audio before ASR inference.",
    ),
    "preprocess_ms": _metric(
        "preprocess_ms",
        "Preprocess",
        "ms",
        "latency",
        "lower",
        "Provider-side preprocessing latency before the inference stage.",
    ),
    "inference_ms": _metric(
        "inference_ms",
        "Inference",
        "ms",
        "latency",
        "lower",
        "Core model inference latency.",
    ),
    "postprocess_ms": _metric(
        "postprocess_ms",
        "Postprocess",
        "ms",
        "latency",
        "lower",
        "Provider-side postprocessing latency after inference.",
    ),
    "ros_service_latency_ms": _metric(
        "ros_service_latency_ms",
        "ROS Service Latency",
        "ms",
        "latency",
        "lower",
        "ROS service roundtrip latency used by runtime recognition diagnostics.",
    ),
    "measured_audio_duration_sec": _metric(
        "measured_audio_duration_sec",
        "Measured Audio Duration",
        "sec",
        "diagnostic",
        "higher",
        (
            "Audio duration measured from the processed file or bytes and used "
            "for canonical normalization."
        ),
    ),
    "declared_audio_duration_sec": _metric(
        "declared_audio_duration_sec",
        "Declared Audio Duration",
        "sec",
        "diagnostic",
        "higher",
        "Reference duration declared by the dataset manifest or caller metadata.",
    ),
    "duration_mismatch_sec": _metric(
        "duration_mismatch_sec",
        "Duration Mismatch",
        "sec",
        "diagnostic",
        "lower",
        "Absolute mismatch between measured and declared audio duration.",
    ),
    "audio_duration_sec": _metric(
        "audio_duration_sec",
        "Audio Duration",
        "sec",
        "diagnostic",
        "higher",
        (
            "Effective audio duration used for normalization; canonical flows "
            "prefer measured duration."
        ),
    ),
    "estimated_cost_usd": _metric(
        "estimated_cost_usd",
        "Estimated Cost",
        "usd",
        "cost",
        "lower",
        "Estimated provider cost for the sample using the selected preset pricing metadata.",
    ),
    "success_rate": _metric(
        "success_rate",
        "Success Rate",
        "ratio",
        "reliability",
        "higher",
        "Share of samples completed without degraded/error result.",
        summary_aggregator="rate",
    ),
    "failure_rate": _metric(
        "failure_rate",
        "Failure Rate",
        "ratio",
        "reliability",
        "lower",
        "Share of samples that ended in degraded/error result.",
        summary_aggregator="rate",
    ),
    "timeout_rate": _metric(
        "timeout_rate",
        "Timeout Rate",
        "ratio",
        "reliability",
        "lower",
        "Share of samples whose error_code indicates a timeout.",
        summary_aggregator="rate",
    ),
    "first_partial_latency_ms": _metric(
        "first_partial_latency_ms",
        "First Partial Latency",
        "ms",
        "streaming",
        "lower",
        "Provider-side first partial latency used to derive canonical first-result timing.",
        applicable_execution_modes=("streaming",),
        deprecated=True,
    ),
    "finalization_latency_ms": _metric(
        "finalization_latency_ms",
        "Finalization Latency",
        "ms",
        "streaming",
        "lower",
        "Wall-clock latency between stop request and final transcript availability.",
        applicable_execution_modes=("streaming",),
    ),
    "partial_count": _metric(
        "partial_count",
        "Partial Count",
        "count",
        "streaming",
        "higher",
        "Number of distinct partial transcript updates observed during a streaming run.",
        applicable_execution_modes=("streaming",),
    ),
    "cpu_percent_mean": _metric(
        "cpu_percent_mean",
        "CPU Usage Mean",
        "percent",
        "resource",
        "lower",
        "Mean host CPU utilization sampled during the request lifetime.",
        summary_aggregator="duration_weighted_mean",
        summary_weight_metric="end_to_end_latency_ms",
    ),
    "cpu_percent_peak": _metric(
        "cpu_percent_peak",
        "CPU Usage Peak",
        "percent",
        "resource",
        "lower",
        "Peak host CPU utilization sampled during the request lifetime.",
        summary_aggregator="max",
    ),
    "memory_mb_mean": _metric(
        "memory_mb_mean",
        "Memory Mean",
        "mb",
        "resource",
        "lower",
        "Mean resident memory sampled during the request lifetime.",
        summary_aggregator="duration_weighted_mean",
        summary_weight_metric="end_to_end_latency_ms",
    ),
    "memory_mb_peak": _metric(
        "memory_mb_peak",
        "Memory Peak",
        "mb",
        "resource",
        "lower",
        "Peak resident memory sampled during the request lifetime.",
        summary_aggregator="max",
    ),
    "gpu_util_percent_mean": _metric(
        "gpu_util_percent_mean",
        "GPU Usage Mean",
        "percent",
        "resource",
        "lower",
        "Mean NVIDIA GPU utilization sampled during the request lifetime when available.",
        summary_aggregator="duration_weighted_mean",
        summary_weight_metric="end_to_end_latency_ms",
    ),
    "gpu_util_percent_peak": _metric(
        "gpu_util_percent_peak",
        "GPU Usage Peak",
        "percent",
        "resource",
        "lower",
        "Peak NVIDIA GPU utilization sampled during the request lifetime when available.",
        summary_aggregator="max",
    ),
    "gpu_memory_mb_mean": _metric(
        "gpu_memory_mb_mean",
        "GPU Memory Mean",
        "mb",
        "resource",
        "lower",
        "Mean NVIDIA GPU memory sampled during the request lifetime when available.",
        summary_aggregator="duration_weighted_mean",
        summary_weight_metric="end_to_end_latency_ms",
    ),
    "gpu_memory_mb_peak": _metric(
        "gpu_memory_mb_peak",
        "GPU Memory Peak",
        "mb",
        "resource",
        "lower",
        "Peak NVIDIA GPU memory sampled during the request lifetime when available.",
        summary_aggregator="max",
    ),
    "cpu_percent": _metric(
        "cpu_percent",
        "CPU Usage",
        "percent",
        "resource",
        "lower",
        "Deprecated alias of cpu_percent_mean.",
        deprecated=True,
        alias_of="cpu_percent_mean",
    ),
    "memory_mb": _metric(
        "memory_mb",
        "Memory",
        "mb",
        "resource",
        "lower",
        "Deprecated alias of memory_mb_mean.",
        deprecated=True,
        alias_of="memory_mb_mean",
    ),
    "gpu_util_percent": _metric(
        "gpu_util_percent",
        "GPU Usage",
        "percent",
        "resource",
        "lower",
        "Deprecated alias of gpu_util_percent_mean.",
        deprecated=True,
        alias_of="gpu_util_percent_mean",
    ),
    "gpu_memory_mb": _metric(
        "gpu_memory_mb",
        "GPU Memory",
        "mb",
        "resource",
        "lower",
        "Deprecated alias of gpu_memory_mb_mean.",
        deprecated=True,
        alias_of="gpu_memory_mb_mean",
    ),
}


def metric_definition(name: str) -> MetricDefinition | None:
    """Return the canonical metric definition for a name, if it exists."""
    return METRIC_DEFINITIONS.get(str(name or "").strip())


def metric_metadata(names: list[str] | tuple[str, ...] | set[str]) -> dict[str, dict[str, object]]:
    """Return serialized metadata for the requested subset of metrics."""
    payload: dict[str, dict[str, object]] = {}
    for name in names:
        definition = metric_definition(str(name))
        if definition is None:
            continue
        payload[definition.name] = definition.as_dict()
    return payload


def validate_metric_names(names: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    """Validate metric names against the registry and return unknown-name errors."""
    unknown = sorted({str(name).strip() for name in names if metric_definition(str(name)) is None})
    return [f"Unknown metric: {name}" for name in unknown]


def metric_preference(name: str) -> str:
    """Return whether higher or lower values are considered better for a metric."""
    definition = metric_definition(name)
    if definition is None:
        return "higher"
    return definition.preferred_direction


def metric_applicable(name: str, *, execution_mode: str) -> bool:
    """Return whether a metric is meaningful for the requested execution mode."""
    definition = metric_definition(name)
    if definition is None:
        return False
    return execution_mode in definition.applicable_execution_modes
