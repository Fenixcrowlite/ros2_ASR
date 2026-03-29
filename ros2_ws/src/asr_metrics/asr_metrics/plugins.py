"""Plugin-style benchmark metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from asr_metrics.quality import cer, wer


@dataclass(slots=True)
class MetricContext:
    reference_text: str
    hypothesis_text: str
    latency_ms: float
    success: bool
    audio_duration_sec: float = 0.0
    estimated_cost_usd: float = 0.0
    first_partial_latency_ms: float = 0.0
    finalization_latency_ms: float = 0.0
    partial_count: int = 0


class MetricPlugin(ABC):
    name = "metric"

    @abstractmethod
    def compute(self, context: MetricContext) -> float:
        raise NotImplementedError


class WerMetric(MetricPlugin):
    name = "wer"

    def compute(self, context: MetricContext) -> float:
        return float(wer(context.reference_text, context.hypothesis_text))


class CerMetric(MetricPlugin):
    name = "cer"

    def compute(self, context: MetricContext) -> float:
        return float(cer(context.reference_text, context.hypothesis_text))


class LatencyMetric(MetricPlugin):
    name = "total_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.latency_ms)


class PerUtteranceLatencyMetric(MetricPlugin):
    name = "per_utterance_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.latency_ms)


class RealTimeFactorMetric(MetricPlugin):
    name = "real_time_factor"

    def compute(self, context: MetricContext) -> float:
        duration = max(float(context.audio_duration_sec or 0.0), 0.001)
        return float(context.latency_ms / 1000.0) / duration


class EstimatedCostMetric(MetricPlugin):
    name = "estimated_cost_usd"

    def compute(self, context: MetricContext) -> float:
        return float(context.estimated_cost_usd)


class FirstPartialLatencyMetric(MetricPlugin):
    name = "first_partial_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.first_partial_latency_ms)


class FinalizationLatencyMetric(MetricPlugin):
    name = "finalization_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.finalization_latency_ms)


class PartialCountMetric(MetricPlugin):
    name = "partial_count"

    def compute(self, context: MetricContext) -> float:
        return float(context.partial_count)


class SuccessMetric(MetricPlugin):
    name = "success_rate"

    def compute(self, context: MetricContext) -> float:
        return 1.0 if context.success else 0.0


class FailureMetric(MetricPlugin):
    name = "failure_rate"

    def compute(self, context: MetricContext) -> float:
        return 0.0 if context.success else 1.0


class SampleAccuracyMetric(MetricPlugin):
    name = "sample_accuracy"

    def compute(self, context: MetricContext) -> float:
        return 1.0 if cer(context.reference_text, context.hypothesis_text) == 0.0 else 0.0


DEFAULT_PLUGINS: dict[str, MetricPlugin] = {
    WerMetric.name: WerMetric(),
    CerMetric.name: CerMetric(),
    LatencyMetric.name: LatencyMetric(),
    PerUtteranceLatencyMetric.name: PerUtteranceLatencyMetric(),
    RealTimeFactorMetric.name: RealTimeFactorMetric(),
    EstimatedCostMetric.name: EstimatedCostMetric(),
    FirstPartialLatencyMetric.name: FirstPartialLatencyMetric(),
    FinalizationLatencyMetric.name: FinalizationLatencyMetric(),
    PartialCountMetric.name: PartialCountMetric(),
    SuccessMetric.name: SuccessMetric(),
    FailureMetric.name: FailureMetric(),
    SampleAccuracyMetric.name: SampleAccuracyMetric(),
}
