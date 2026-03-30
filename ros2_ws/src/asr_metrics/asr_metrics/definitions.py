"""Metric registry with semantics used by benchmarks, reports, and UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    name: str
    display_name: str
    unit: str
    category: str
    preferred_direction: str
    description: str
    summary_aggregator: str = "mean"
    applicable_execution_modes: tuple[str, ...] = ("batch", "streaming")

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "wer": MetricDefinition(
        name="wer",
        display_name="WER",
        unit="ratio",
        category="quality",
        preferred_direction="lower",
        description="Corpus-level word error rate against the normalized reference transcript.",
        summary_aggregator="corpus_rate",
    ),
    "cer": MetricDefinition(
        name="cer",
        display_name="CER",
        unit="ratio",
        category="quality",
        preferred_direction="lower",
        description="Corpus-level character error rate after normalization and whitespace removal.",
        summary_aggregator="corpus_rate",
    ),
    "sample_accuracy": MetricDefinition(
        name="sample_accuracy",
        display_name="Sample Accuracy",
        unit="ratio",
        category="quality",
        preferred_direction="higher",
        description="Share of samples whose normalized reference and hypothesis match exactly.",
        summary_aggregator="rate",
    ),
    "total_latency_ms": MetricDefinition(
        name="total_latency_ms",
        display_name="Total Latency",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="End-to-end latency for the sample or utterance.",
    ),
    "per_utterance_latency_ms": MetricDefinition(
        name="per_utterance_latency_ms",
        display_name="Per-Utterance Latency",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description=(
            "Alias of total latency retained for backward-compatible dashboards and exports."
        ),
    ),
    "real_time_factor": MetricDefinition(
        name="real_time_factor",
        display_name="RTF",
        unit="ratio",
        category="latency",
        preferred_direction="lower",
        description="Processing time divided by audio duration.",
    ),
    "confidence": MetricDefinition(
        name="confidence",
        display_name="Confidence",
        unit="ratio",
        category="quality",
        preferred_direction="higher",
        description="Average confidence exposed by the provider for the recognized utterance.",
    ),
    "audio_load_ms": MetricDefinition(
        name="audio_load_ms",
        display_name="Audio Load",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="Time spent loading or materializing input audio before ASR inference.",
    ),
    "preprocess_ms": MetricDefinition(
        name="preprocess_ms",
        display_name="Preprocess",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="Provider-side preprocessing latency before the inference stage.",
    ),
    "inference_ms": MetricDefinition(
        name="inference_ms",
        display_name="Inference",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="Core model inference latency.",
    ),
    "postprocess_ms": MetricDefinition(
        name="postprocess_ms",
        display_name="Postprocess",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="Provider-side postprocessing latency after inference.",
    ),
    "time_to_result_ms": MetricDefinition(
        name="time_to_result_ms",
        display_name="Time To Result",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="Observed wall-clock time from request start to final result availability.",
    ),
    "ros_service_latency_ms": MetricDefinition(
        name="ros_service_latency_ms",
        display_name="ROS Service Latency",
        unit="ms",
        category="latency",
        preferred_direction="lower",
        description="End-to-end latency of the ROS service roundtrip used by runtime recognition.",
    ),
    "estimated_cost_usd": MetricDefinition(
        name="estimated_cost_usd",
        display_name="Estimated Cost",
        unit="usd",
        category="cost",
        preferred_direction="lower",
        description=(
            "Estimated provider cost for the sample using the selected preset pricing metadata."
        ),
    ),
    "success_rate": MetricDefinition(
        name="success_rate",
        display_name="Success Rate",
        unit="ratio",
        category="reliability",
        preferred_direction="higher",
        description="Share of samples completed without degraded/error result.",
        summary_aggregator="rate",
    ),
    "failure_rate": MetricDefinition(
        name="failure_rate",
        display_name="Failure Rate",
        unit="ratio",
        category="reliability",
        preferred_direction="lower",
        description="Share of samples that ended in degraded/error result.",
        summary_aggregator="rate",
    ),
    "first_partial_latency_ms": MetricDefinition(
        name="first_partial_latency_ms",
        display_name="First Partial Latency",
        unit="ms",
        category="streaming",
        preferred_direction="lower",
        description="Latency from stream start to the first emitted partial transcript.",
        applicable_execution_modes=("streaming",),
    ),
    "finalization_latency_ms": MetricDefinition(
        name="finalization_latency_ms",
        display_name="Finalization Latency",
        unit="ms",
        category="streaming",
        preferred_direction="lower",
        description=(
            "Latency between stop request and final transcript availability for streaming runs."
        ),
        applicable_execution_modes=("streaming",),
    ),
    "partial_count": MetricDefinition(
        name="partial_count",
        display_name="Partial Count",
        unit="count",
        category="streaming",
        preferred_direction="higher",
        description="Number of distinct partial updates observed during a streaming run.",
        applicable_execution_modes=("streaming",),
    ),
    "cpu_percent": MetricDefinition(
        name="cpu_percent",
        display_name="CPU Usage",
        unit="percent",
        category="resource",
        preferred_direction="lower",
        description="Host CPU utilization sampled during the run.",
    ),
    "memory_mb": MetricDefinition(
        name="memory_mb",
        display_name="Memory",
        unit="mb",
        category="resource",
        preferred_direction="lower",
        description="Resident memory sampled during the run.",
    ),
    "gpu_util_percent": MetricDefinition(
        name="gpu_util_percent",
        display_name="GPU Usage",
        unit="percent",
        category="resource",
        preferred_direction="lower",
        description="NVIDIA GPU utilization sampled during the run when available.",
    ),
    "gpu_memory_mb": MetricDefinition(
        name="gpu_memory_mb",
        display_name="GPU Memory",
        unit="mb",
        category="resource",
        preferred_direction="lower",
        description="NVIDIA GPU memory sampled during the run when available.",
    ),
}


def metric_definition(name: str) -> MetricDefinition | None:
    return METRIC_DEFINITIONS.get(str(name or "").strip())


def metric_metadata(names: list[str] | tuple[str, ...] | set[str]) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for name in names:
        definition = metric_definition(str(name))
        if definition is None:
            continue
        payload[definition.name] = definition.as_dict()
    return payload


def validate_metric_names(names: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    unknown = sorted({str(name).strip() for name in names if metric_definition(str(name)) is None})
    return [f"Unknown metric: {name}" for name in unknown]


def metric_preference(name: str) -> str:
    definition = metric_definition(name)
    if definition is None:
        return "higher"
    return definition.preferred_direction


def metric_applicable(name: str, *, execution_mode: str) -> bool:
    definition = metric_definition(name)
    if definition is None:
        return False
    return execution_mode in definition.applicable_execution_modes
