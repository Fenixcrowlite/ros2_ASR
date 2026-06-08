"""Summary helpers for benchmark result rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from asr_metrics.definitions import metric_applicable, metric_definition, metric_metadata
from asr_metrics.quality import text_quality_support
from asr_metrics.semantics import METRICS_SEMANTICS_VERSION, metric_semantics_version


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = max(0.0, min(1.0, percentile)) * float(len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return float(sorted_values[lower] + ((sorted_values[upper] - sorted_values[lower]) * weight))


def _int_if_whole(value: float) -> int | float:
    return int(value) if float(value).is_integer() else float(value)


def _scalar_statistics(values: list[float], *, aggregator: str = "mean") -> dict[str, Any]:
    ordered = sorted(float(item) for item in values)
    return {
        "count": len(ordered),
        "aggregator": aggregator,
        "sum": float(sum(ordered)),
        "mean": float(mean(ordered)),
        "min": float(ordered[0]),
        "max": float(ordered[-1]),
        "p50": _percentile(ordered, 0.50),
        "p95": _percentile(ordered, 0.95),
        "p99": _percentile(ordered, 0.99),
        "value": float(mean(ordered)),
    }


def _rate_statistics(values: list[float]) -> dict[str, Any]:
    numerator = float(sum(values))
    denominator = len(values)
    value = numerator / float(denominator) if denominator > 0 else 0.0
    return {
        "count": denominator,
        "aggregator": "rate",
        "numerator": _int_if_whole(numerator),
        "denominator": denominator,
        "value": value,
    }


def _sum_statistics(values: list[float]) -> dict[str, Any]:
    total = float(sum(values))
    return {
        "count": len(values),
        "aggregator": "sum",
        "sum": total,
        "value": total,
    }


def _max_statistics(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "aggregator": "max",
        "max": float(max(values)),
        "value": float(max(values)),
    }


def _duration_weighted_mean_statistics(
    values: list[float],
    weights: list[float],
) -> dict[str, Any]:
    if not values or not weights or len(values) != len(weights):
        return _scalar_statistics(values, aggregator="duration_weighted_mean")
    usable = [
        (value, weight)
        for value, weight in zip(values, weights, strict=False)
        if weight > 0.0
    ]
    if not usable:
        return _scalar_statistics(values, aggregator="duration_weighted_mean")
    numerator = sum(value * weight for value, weight in usable)
    denominator = sum(weight for _, weight in usable)
    weighted_mean = numerator / denominator if denominator > 0 else 0.0
    ordered = sorted(value for value, _ in usable)
    return {
        "count": len(usable),
        "aggregator": "duration_weighted_mean",
        "weighted_sum": float(numerator),
        "weight_total": float(denominator),
        "mean": float(weighted_mean),
        "min": float(ordered[0]),
        "max": float(ordered[-1]),
        "p50": _percentile(ordered, 0.50),
        "p95": _percentile(ordered, 0.95),
        "p99": _percentile(ordered, 0.99),
        "value": float(weighted_mean),
    }


def _support_int(item: dict[str, Any], *names: str) -> int:
    for name in names:
        value = item.get(name)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _support_float(item: dict[str, Any], name: str) -> float:
    value = _coerce_float(item.get(name))
    return value if value is not None else 0.0


def _alignment_totals(quality_supports: list[dict[str, Any]]) -> dict[str, int]:
    hits = sum(_support_int(item, "hits", "word_hits") for item in quality_supports)
    substitutions = sum(
        _support_int(item, "substitutions", "word_substitutions") for item in quality_supports
    )
    deletions = sum(_support_int(item, "deletions", "word_deletions") for item in quality_supports)
    insertions = sum(
        _support_int(item, "insertions", "word_insertions") for item in quality_supports
    )
    return {
        "hits": hits,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
    }


def _quality_stat(
    *,
    quality_supports: list[dict[str, Any]],
    numerator: float,
    denominator: float,
    aggregator: str,
    value: float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    resolved = float(value) if value is not None else (
        float(numerator) / float(denominator) if denominator > 0 else 0.0
    )
    return {
        "count": len(quality_supports),
        "aggregator": aggregator,
        "numerator": _int_if_whole(float(numerator)),
        "denominator": _int_if_whole(float(denominator)),
        "value": resolved,
        **extra,
    }


def _metric_groups(
    mean_metrics: dict[str, float],
    metric_statistics: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float]]:
    quality_metrics: dict[str, float] = {}
    latency_metrics: dict[str, float] = {}
    reliability_metrics: dict[str, float] = {}
    cost_metrics: dict[str, float] = {}
    cost_totals: dict[str, float] = {}
    streaming_metrics: dict[str, float] = {}
    resource_metrics: dict[str, float] = {}
    diagnostic_metrics: dict[str, float] = {}
    other_metrics: dict[str, float] = {}

    for name, value in sorted(mean_metrics.items()):
        definition = metric_definition(name)
        if definition is None:
            other_metrics[name] = value
            continue
        if definition.category == "quality":
            quality_metrics[name] = value
        elif definition.category == "latency":
            latency_metrics[name] = value
        elif definition.category == "reliability":
            reliability_metrics[name] = value
        elif definition.category == "cost":
            cost_metrics[name] = value
        elif definition.category == "streaming":
            streaming_metrics[name] = value
        elif definition.category == "resource":
            resource_metrics[name] = value
        elif definition.category == "diagnostic":
            diagnostic_metrics[name] = value
        else:
            other_metrics[name] = value

    for name in sorted(cost_metrics):
        stats = metric_statistics.get(name, {})
        if not isinstance(stats, dict):
            continue
        total = _coerce_float(stats.get("sum"))
        if total is None:
            total = _coerce_float(stats.get("value"))
        if total is not None:
            cost_totals[name] = total

    grouped = {
        "quality_metrics": quality_metrics,
        "latency_metrics": latency_metrics,
        "reliability_metrics": reliability_metrics,
        "cost_metrics": cost_metrics,
        "cost_totals": cost_totals,
        "streaming_metrics": streaming_metrics,
        "resource_metrics": resource_metrics,
        "diagnostic_metrics": diagnostic_metrics,
    }
    if other_metrics:
        grouped["other_metrics"] = other_metrics
    return grouped


def summarize_result_rows(
    rows: list[dict[str, Any]], *, exclude_corrupted: bool = False
) -> dict[str, Any]:
    """Build logically-clean aggregates from benchmark result rows."""

    total_samples = len(rows)
    successful_samples = sum(1 for row in rows if bool(row.get("success")))
    failed_samples = total_samples - successful_samples
    aggregate_rows = (
        [row for row in rows if not bool(row.get("trace_corrupted"))]
        if exclude_corrupted
        else list(rows)
    )
    aggregate_samples = len(aggregate_rows)
    corrupted_samples = total_samples - aggregate_samples
    warning_samples = sum(
        1
        for row in aggregate_rows
        if bool(row.get("trace_warnings"))
        or int(row.get("trace_warning_count", 0) or 0) > 0
        or bool(row.get("warning_messages"))
    )
    error_codes = Counter(
        str(row.get("error_code", "") or "").strip()
        for row in aggregate_rows
        if str(row.get("error_code", "") or "").strip()
    )

    enabled_metric_names: set[str] = set()
    metric_values: dict[str, list[float]] = defaultdict(list)
    metric_weights: dict[str, list[float]] = defaultdict(list)
    quality_supports: list[dict[str, Any]] = []

    semantics_versions = sorted(
        {
            int(metric_semantics_version(row))
            for row in rows
        }
    )
    mixed_semantics = len(semantics_versions) > 1
    unsupported_semantics = any(version < METRICS_SEMANTICS_VERSION for version in semantics_versions)

    for row in aggregate_rows:
        row_metrics = row.get("metrics", {})
        execution_mode = str(row.get("execution_mode", "batch") or "batch")
        if isinstance(row_metrics, dict):
            for name, value in row_metrics.items():
                metric_name = str(name or "").strip()
                if not metric_name or not metric_applicable(
                    metric_name,
                    execution_mode=execution_mode,
                ):
                    continue
                enabled_metric_names.add(metric_name)
                coerced = _coerce_float(value)
                if coerced is None:
                    continue
                metric_values[metric_name].append(coerced)
                definition = metric_definition(metric_name)
                if (
                    definition is not None
                    and definition.summary_aggregator == "duration_weighted_mean"
                ):
                    weight_value = _coerce_float(
                        row_metrics.get(definition.summary_weight_metric)
                        if definition.summary_weight_metric
                        else None
                    )
                    metric_weights[metric_name].append(
                        weight_value if weight_value and weight_value > 0 else 1.0
                    )

        support_payload = row.get("quality_support")
        if isinstance(support_payload, dict):
            quality_supports.append(dict(support_payload))
            continue

        quality_metric_names = {
            "wer",
            "cer",
            "sample_accuracy",
            "ser",
            "mer",
            "wil",
            "wip",
            "micro_wer",
            "macro_wer",
            "micro_cer",
            "macro_cer",
            "hallucination_on_silence",
        }
        if any(metric_name in enabled_metric_names for metric_name in quality_metric_names):
            support = text_quality_support(
                str(row.get("reference_text", "") or ""),
                str(row.get("text", "") or ""),
            )
            quality_supports.append(support.as_dict())

    mean_metrics: dict[str, float] = {}
    metric_counts: dict[str, int] = {}
    metric_statistics: dict[str, dict[str, Any]] = {}

    for metric_name in sorted(enabled_metric_names):
        if metric_name in {
            "wer",
            "cer",
            "sample_accuracy",
            "ser",
            "mer",
            "wil",
            "wip",
            "micro_wer",
            "macro_wer",
            "micro_cer",
            "macro_cer",
            "hallucination_on_silence",
        } and quality_supports:
            if metric_name in {"wer", "micro_wer"}:
                numerator = sum(_support_int(item, "word_edits") for item in quality_supports)
                denominator = sum(
                    _support_int(item, "reference_word_count") for item in quality_supports
                )
                value = float(numerator) / float(denominator) if denominator > 0 else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = len(quality_supports)
                metric_statistics[metric_name] = _quality_stat(
                    quality_supports=quality_supports,
                    numerator=numerator,
                    denominator=denominator,
                    aggregator="corpus_rate",
                    value=value,
                )
                continue
            if metric_name in {"cer", "micro_cer"}:
                numerator = sum(_support_int(item, "char_edits") for item in quality_supports)
                denominator = sum(
                    _support_int(item, "reference_char_count") for item in quality_supports
                )
                value = float(numerator) / float(denominator) if denominator > 0 else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = len(quality_supports)
                metric_statistics[metric_name] = _quality_stat(
                    quality_supports=quality_supports,
                    numerator=numerator,
                    denominator=denominator,
                    aggregator="corpus_rate",
                    value=value,
                )
                continue
            if metric_name == "macro_wer":
                values = [
                    _support_float(item, "wer")
                    for item in quality_supports
                    if _support_int(item, "reference_word_count") > 0
                ]
                value = float(mean(values)) if values else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = len(values)
                metric_statistics[metric_name] = {
                    "count": len(values),
                    "aggregator": "macro_mean",
                    "value": value,
                }
                continue
            if metric_name == "macro_cer":
                values = [
                    _support_float(item, "cer")
                    for item in quality_supports
                    if _support_int(item, "reference_char_count") > 0
                ]
                value = float(mean(values)) if values else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = len(values)
                metric_statistics[metric_name] = {
                    "count": len(values),
                    "aggregator": "macro_mean",
                    "value": value,
                }
                continue
            exact_matches = sum(1 for item in quality_supports if bool(item.get("exact_match")))
            count = len(quality_supports)
            if metric_name == "sample_accuracy":
                numerator = exact_matches
                denominator = count
                value = float(numerator) / float(denominator) if denominator > 0 else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = count
                metric_statistics[metric_name] = _quality_stat(
                    quality_supports=quality_supports,
                    numerator=numerator,
                    denominator=denominator,
                    aggregator="rate",
                    value=value,
                )
                continue
            if metric_name == "ser":
                numerator = count - exact_matches
                denominator = count
                value = float(numerator) / float(denominator) if denominator > 0 else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = count
                metric_statistics[metric_name] = _quality_stat(
                    quality_supports=quality_supports,
                    numerator=numerator,
                    denominator=denominator,
                    aggregator="rate",
                    value=value,
                )
                continue
            if metric_name == "hallucination_on_silence":
                numerator = sum(
                    1
                    for item in quality_supports
                    if bool(item.get("hallucination_on_silence"))
                )
                denominator = sum(
                    1 for item in quality_supports if not bool(item.get("reference_has_content"))
                )
                value = float(numerator) / float(denominator) if denominator > 0 else 0.0
                mean_metrics[metric_name] = value
                metric_counts[metric_name] = denominator
                metric_statistics[metric_name] = _quality_stat(
                    quality_supports=quality_supports,
                    numerator=numerator,
                    denominator=denominator,
                    aggregator="rate",
                    value=value,
                )
                continue
            totals = _alignment_totals(quality_supports)
            h = totals["hits"]
            s = totals["substitutions"]
            d = totals["deletions"]
            i = totals["insertions"]
            if metric_name == "mer":
                alignment_denominator = float(h + s + d + i)
                value = (
                    float(s + d + i) / alignment_denominator
                    if alignment_denominator > 0
                    else 0.0
                )
                alignment_numerator = float(s + d + i)
            else:
                recall_denominator = h + s + d
                precision_denominator = h + s + i
                wip = (
                    (float(h) / float(recall_denominator))
                    * (float(h) / float(precision_denominator))
                    if recall_denominator > 0 and precision_denominator > 0
                    else 0.0
                )
                value = wip if metric_name == "wip" else 1.0 - wip
                alignment_numerator = float(value)
                alignment_denominator = 1.0
            mean_metrics[metric_name] = value
            metric_counts[metric_name] = len(quality_supports)
            metric_statistics[metric_name] = _quality_stat(
                quality_supports=quality_supports,
                numerator=alignment_numerator,
                denominator=alignment_denominator,
                aggregator="alignment_rate",
                value=value,
                **totals,
            )
            continue

        if metric_name == "timeout_rate":
            timeout_samples = sum(
                count for code, count in error_codes.items() if "timeout" in code.lower()
            )
            denominator = len(aggregate_rows)
            value = float(timeout_samples) / float(denominator) if denominator else 0.0
            mean_metrics[metric_name] = value
            metric_counts[metric_name] = denominator
            metric_statistics[metric_name] = {
                "count": denominator,
                "aggregator": "rate",
                "numerator": timeout_samples,
                "denominator": denominator,
                "value": value,
            }
            continue

        series = metric_values.get(metric_name, [])
        if not series:
            continue
        definition = metric_definition(metric_name)
        aggregator = definition.summary_aggregator if definition is not None else "mean"
        metric_counts[metric_name] = len(series)
        if aggregator == "rate":
            metric_statistics[metric_name] = _rate_statistics(series)
        elif aggregator == "sum":
            metric_statistics[metric_name] = _sum_statistics(series)
        elif aggregator == "max":
            metric_statistics[metric_name] = _max_statistics(series)
        elif aggregator == "duration_weighted_mean":
            metric_statistics[metric_name] = _duration_weighted_mean_statistics(
                series,
                metric_weights.get(metric_name, []),
            )
        else:
            metric_statistics[metric_name] = _scalar_statistics(series, aggregator=aggregator)
        mean_metrics[metric_name] = float(metric_statistics[metric_name]["value"])

    return {
        "metrics_semantics_version": METRICS_SEMANTICS_VERSION,
        "unsupported_semantics": unsupported_semantics,
        "mixed_semantics": mixed_semantics,
        "samples": total_samples,
        "total_samples": total_samples,
        "successful_samples": successful_samples,
        "failed_samples": failed_samples,
        "aggregate_samples": aggregate_samples,
        "warning_samples": warning_samples,
        "top_error_codes": [
            {"error_code": code, "count": count} for code, count in error_codes.most_common()
        ],
        "mean_metrics": mean_metrics,
        "metric_counts": metric_counts,
        "metric_statistics": metric_statistics,
        "metric_metadata": metric_metadata(sorted(enabled_metric_names)),
        "aggregate_excludes_corrupted": exclude_corrupted,
        "corrupted_samples": corrupted_samples,
        **_metric_groups(mean_metrics, metric_statistics),
    }
