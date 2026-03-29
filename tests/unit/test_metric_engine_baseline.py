from __future__ import annotations

import pytest
from asr_metrics.engine import MetricEngine
from asr_metrics.plugins import MetricContext
from asr_metrics.quality import cer, normalize_text, text_quality_support, wer


def test_text_quality_metrics_handle_exact_and_empty_cases() -> None:
    assert normalize_text("  Hello   WORLD ") == "hello world"
    assert normalize_text(" Zero. ") == "zero"
    assert normalize_text("one, two!") == "one two"
    assert wer("hello world", "hello world") == 0.0
    assert wer("zero", "Zero.") == 0.0
    assert cer("hello world", "hello world") == 0.0
    assert cer("one", "One.") == 0.0
    assert wer("", "") == 0.0
    assert cer("", "speech") == 1.0


def test_metric_engine_rejects_unknown_metrics() -> None:
    with pytest.raises(ValueError, match="Unknown metric: unknown"):
        MetricEngine(enabled_metrics=["wer", "cer", "unknown"])


def test_metric_engine_evaluates_enabled_metrics() -> None:
    engine = MetricEngine(enabled_metrics=["wer", "cer", "sample_accuracy", "total_latency_ms"])
    result = engine.evaluate(
        MetricContext(
            reference_text="hello world",
            hypothesis_text="hello world",
            latency_ms=17.5,
            success=True,
            quality_support=text_quality_support("hello world", "hello world"),
        )
    )

    assert result["wer"] == 0.0
    assert result["cer"] == 0.0
    assert result["sample_accuracy"] == 1.0
    assert result["total_latency_ms"] == 17.5


def test_metric_engine_reports_failure_and_non_exact_match() -> None:
    engine = MetricEngine(enabled_metrics=["failure_rate", "success_rate", "sample_accuracy"])
    result = engine.evaluate(
        MetricContext(
            reference_text="hello world",
            hypothesis_text="yellow world",
            latency_ms=99.0,
            success=False,
        )
    )

    assert result["failure_rate"] == 1.0
    assert result["success_rate"] == 0.0
    assert result["sample_accuracy"] == 0.0


def test_sample_accuracy_requires_exact_normalized_match_not_space_free_cer() -> None:
    support = text_quality_support("10001 90210 01803", "100019021001803.")

    assert support.cer == 0.0
    assert support.wer == 1.0
    assert support.exact_match is False

    engine = MetricEngine(enabled_metrics=["sample_accuracy"])
    result = engine.evaluate(
        MetricContext(
            reference_text="10001 90210 01803",
            hypothesis_text="100019021001803.",
            latency_ms=1.0,
            success=True,
            quality_support=support,
        )
    )

    assert result["sample_accuracy"] == 0.0
