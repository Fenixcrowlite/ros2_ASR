"""Plugin-style benchmark metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from asr_metrics.quality import cer, wer


@dataclass(slots=True)
class MetricContext:
    reference_text: str
    hypothesis_text: str
    latency_ms: float
    success: bool


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
    SuccessMetric.name: SuccessMetric(),
    FailureMetric.name: FailureMetric(),
    SampleAccuracyMetric.name: SampleAccuracyMetric(),
}
