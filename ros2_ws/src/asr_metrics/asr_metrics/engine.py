"""Metric engine executing selected plugin metrics."""

from __future__ import annotations

from asr_metrics.plugins import DEFAULT_PLUGINS, MetricContext


class MetricEngine:
    def __init__(self, enabled_metrics: list[str] | None = None) -> None:
        self.enabled_metrics = enabled_metrics or ["wer", "cer", "total_latency_ms", "success_rate"]

    def evaluate(self, context: MetricContext) -> dict[str, float]:
        result: dict[str, float] = {}
        for metric_name in self.enabled_metrics:
            plugin = DEFAULT_PLUGINS.get(metric_name)
            if plugin is None:
                continue
            result[metric_name] = float(plugin.compute(context))
        return result
