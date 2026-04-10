"""Plugin-style benchmark metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from asr_metrics.quality import TextQualitySupport, text_quality_support


@dataclass(slots=True)
class MetricContext:
    reference_text: str
    hypothesis_text: str
    success: bool
    execution_mode: str = "batch"
    latency_ms: float = 0.0
    audio_duration_sec: float = 0.0
    provider_compute_latency_ms: float = 0.0
    end_to_end_latency_ms: float = 0.0
    measured_audio_duration_sec: float = 0.0
    estimated_cost_usd: float = 0.0
    first_partial_latency_ms: float = 0.0
    time_to_first_result_ms: float = 0.0
    time_to_final_result_ms: float = 0.0
    finalization_latency_ms: float = 0.0
    partial_count: int = 0
    quality_support: TextQualitySupport | None = None

    def __post_init__(self) -> None:
        if self.provider_compute_latency_ms <= 0.0 and self.latency_ms > 0.0:
            self.provider_compute_latency_ms = float(self.latency_ms)
        if self.end_to_end_latency_ms <= 0.0 and self.provider_compute_latency_ms > 0.0:
            self.end_to_end_latency_ms = float(self.provider_compute_latency_ms)
        if self.measured_audio_duration_sec <= 0.0 and self.audio_duration_sec > 0.0:
            self.measured_audio_duration_sec = float(self.audio_duration_sec)
        if self.time_to_first_result_ms <= 0.0 and self.end_to_end_latency_ms > 0.0:
            self.time_to_first_result_ms = float(self.end_to_end_latency_ms)
        if self.time_to_final_result_ms <= 0.0 and self.end_to_end_latency_ms > 0.0:
            self.time_to_final_result_ms = float(self.end_to_end_latency_ms)


class MetricPlugin(ABC):
    name = "metric"

    @abstractmethod
    def compute(self, context: MetricContext) -> float:
        raise NotImplementedError


class WerMetric(MetricPlugin):
    name = "wer"

    def compute(self, context: MetricContext) -> float:
        support = context.quality_support or text_quality_support(
            context.reference_text,
            context.hypothesis_text,
        )
        return float(support.wer)


class CerMetric(MetricPlugin):
    name = "cer"

    def compute(self, context: MetricContext) -> float:
        support = context.quality_support or text_quality_support(
            context.reference_text,
            context.hypothesis_text,
        )
        return float(support.cer)


class ProviderComputeLatencyMetric(MetricPlugin):
    name = "provider_compute_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.provider_compute_latency_ms)


class EndToEndLatencyMetric(MetricPlugin):
    name = "end_to_end_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.end_to_end_latency_ms)


class LatencyMetric(MetricPlugin):
    name = "total_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.provider_compute_latency_ms)


class PerUtteranceLatencyMetric(MetricPlugin):
    name = "per_utterance_latency_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.provider_compute_latency_ms)


class ProviderComputeRtfMetric(MetricPlugin):
    name = "provider_compute_rtf"

    def compute(self, context: MetricContext) -> float:
        duration = max(float(context.measured_audio_duration_sec or 0.0), 0.001)
        return float(context.provider_compute_latency_ms / 1000.0) / duration


class EndToEndRtfMetric(MetricPlugin):
    name = "end_to_end_rtf"

    def compute(self, context: MetricContext) -> float:
        duration = max(float(context.measured_audio_duration_sec or 0.0), 0.001)
        return float(context.end_to_end_latency_ms / 1000.0) / duration


class RealTimeFactorMetric(MetricPlugin):
    name = "real_time_factor"

    def compute(self, context: MetricContext) -> float:
        duration = max(float(context.measured_audio_duration_sec or 0.0), 0.001)
        return float(context.provider_compute_latency_ms / 1000.0) / duration


class TimeToFirstResultMetric(MetricPlugin):
    name = "time_to_first_result_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.time_to_first_result_ms)


class TimeToFinalResultMetric(MetricPlugin):
    name = "time_to_final_result_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.time_to_final_result_ms)


class TimeToResultMetric(MetricPlugin):
    name = "time_to_result_ms"

    def compute(self, context: MetricContext) -> float:
        return float(context.time_to_final_result_ms)


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
        support = context.quality_support
        if support is None:
            support = text_quality_support(context.reference_text, context.hypothesis_text)
        return 1.0 if support.exact_match else 0.0


DEFAULT_PLUGINS: dict[str, MetricPlugin] = {
    WerMetric.name: WerMetric(),
    CerMetric.name: CerMetric(),
    ProviderComputeLatencyMetric.name: ProviderComputeLatencyMetric(),
    EndToEndLatencyMetric.name: EndToEndLatencyMetric(),
    LatencyMetric.name: LatencyMetric(),
    PerUtteranceLatencyMetric.name: PerUtteranceLatencyMetric(),
    ProviderComputeRtfMetric.name: ProviderComputeRtfMetric(),
    EndToEndRtfMetric.name: EndToEndRtfMetric(),
    RealTimeFactorMetric.name: RealTimeFactorMetric(),
    TimeToFirstResultMetric.name: TimeToFirstResultMetric(),
    TimeToFinalResultMetric.name: TimeToFinalResultMetric(),
    TimeToResultMetric.name: TimeToResultMetric(),
    EstimatedCostMetric.name: EstimatedCostMetric(),
    FirstPartialLatencyMetric.name: FirstPartialLatencyMetric(),
    FinalizationLatencyMetric.name: FinalizationLatencyMetric(),
    PartialCountMetric.name: PartialCountMetric(),
    SuccessMetric.name: SuccessMetric(),
    FailureMetric.name: FailureMetric(),
    SampleAccuracyMetric.name: SampleAccuracyMetric(),
}
