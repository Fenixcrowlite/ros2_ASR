"""Metric engine executing selected plugin metrics."""

from __future__ import annotations

from asr_metrics.definitions import metric_applicable, validate_metric_names
from asr_metrics.plugins import DEFAULT_PLUGINS, MetricContext


class MetricEngine:
    def __init__(self, enabled_metrics: list[str] | None = None) -> None:
        requested = enabled_metrics or ["wer", "cer", "total_latency_ms", "success_rate"]
        errors = validate_metric_names(requested)
        if errors:
            raise ValueError("; ".join(errors))
        seen: set[str] = set()
        self.enabled_metrics = []
        for metric_name in requested:
            normalized = str(metric_name).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            self.enabled_metrics.append(normalized)

    def evaluate(self, context: MetricContext) -> dict[str, float]:
        result: dict[str, float] = {}
        for metric_name in self.enabled_metrics:
            if not metric_applicable(
                metric_name, execution_mode=str(context.execution_mode or "batch")
            ):
                continue
            plugin = DEFAULT_PLUGINS.get(metric_name)
            if plugin is None:
                continue
            result[metric_name] = float(plugin.compute(context))
        return result
