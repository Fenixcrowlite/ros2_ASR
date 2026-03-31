from __future__ import annotations

from asr_metrics.summary import summarize_result_rows


def test_summarize_result_rows_uses_corpus_quality_aggregation() -> None:
    rows = [
        {
            "success": True,
            "metrics": {"wer": 1.0, "cer": 1.0, "sample_accuracy": 0.0, "total_latency_ms": 10.0},
            "reference_text": "alpha",
            "text": "beta",
            "quality_support": {
                "normalized_reference": "alpha",
                "normalized_hypothesis": "beta",
                "reference_word_count": 1,
                "reference_char_count": 5,
                "word_edits": 1,
                "char_edits": 4,
                "exact_match": False,
                "wer": 1.0,
                "cer": 0.8,
            },
        },
        {
            "success": True,
            "metrics": {"wer": 0.0, "cer": 0.0, "sample_accuracy": 1.0, "total_latency_ms": 30.0},
            "reference_text": "one two three",
            "text": "one two three",
            "quality_support": {
                "normalized_reference": "one two three",
                "normalized_hypothesis": "one two three",
                "reference_word_count": 3,
                "reference_char_count": 11,
                "word_edits": 0,
                "char_edits": 0,
                "exact_match": True,
                "wer": 0.0,
                "cer": 0.0,
            },
        },
    ]

    summary = summarize_result_rows(rows)

    assert summary["total_samples"] == 2
    assert summary["mean_metrics"]["wer"] == 0.25
    assert round(summary["mean_metrics"]["cer"], 4) == round(4 / 16, 4)
    assert summary["mean_metrics"]["sample_accuracy"] == 0.5
    assert summary["mean_metrics"]["total_latency_ms"] == 20.0
    assert summary["metric_statistics"]["wer"]["aggregator"] == "corpus_rate"
    assert summary["metric_counts"]["wer"] == 2
    assert summary["metric_statistics"]["total_latency_ms"]["sum"] == 40.0


def test_summarize_result_rows_keeps_streaming_only_metrics_out_of_batch_summary() -> None:
    rows = [
        {
            "success": True,
            "metrics": {"wer": 0.0, "estimated_cost_usd": 0.25, "total_latency_ms": 15.0},
            "reference_text": "hello world",
            "text": "hello world",
            "quality_support": {
                "normalized_reference": "hello world",
                "normalized_hypothesis": "hello world",
                "reference_word_count": 2,
                "reference_char_count": 10,
                "word_edits": 0,
                "char_edits": 0,
                "exact_match": True,
                "wer": 0.0,
                "cer": 0.0,
            },
        }
    ]

    summary = summarize_result_rows(rows)

    assert "first_partial_latency_ms" not in summary["mean_metrics"]
    assert "partial_count" not in summary["mean_metrics"]
    assert summary["cost_metrics"]["estimated_cost_usd"] == 0.25
    assert summary["cost_totals"]["estimated_cost_usd"] == 0.25
    assert summary["resource_metrics"] == {}
    assert summary["metric_statistics"]["estimated_cost_usd"]["sum"] == 0.25


def test_summarize_result_rows_uses_rate_statistics_for_reliability_metrics() -> None:
    rows = [
        {"success": True, "metrics": {"success_rate": 1.0, "failure_rate": 0.0}},
        {"success": False, "metrics": {"success_rate": 0.0, "failure_rate": 1.0}},
        {"success": True, "metrics": {"success_rate": 1.0, "failure_rate": 0.0}},
    ]

    summary = summarize_result_rows(rows)

    assert summary["mean_metrics"]["success_rate"] == 2 / 3
    assert summary["mean_metrics"]["failure_rate"] == 1 / 3
    assert summary["metric_statistics"]["success_rate"] == {
        "count": 3,
        "aggregator": "rate",
        "numerator": 2,
        "denominator": 3,
        "value": 2 / 3,
    }
    assert summary["metric_statistics"]["failure_rate"] == {
        "count": 3,
        "aggregator": "rate",
        "numerator": 1,
        "denominator": 3,
        "value": 1 / 3,
    }


def test_summarize_result_rows_excludes_corrupted_rows_from_aggregates() -> None:
    rows = [
        {
            "success": True,
            "trace_corrupted": False,
            "metrics": {"wer": 0.0, "total_latency_ms": 10.0},
            "reference_text": "hello world",
            "text": "hello world",
            "quality_support": {
                "normalized_reference": "hello world",
                "normalized_hypothesis": "hello world",
                "reference_word_count": 2,
                "reference_char_count": 10,
                "word_edits": 0,
                "char_edits": 0,
                "exact_match": True,
                "wer": 0.0,
                "cer": 0.0,
            },
        },
        {
            "success": True,
            "trace_corrupted": True,
            "metrics": {"wer": 1.0, "total_latency_ms": 999.0},
            "reference_text": "hello world",
            "text": "noise",
            "quality_support": {
                "normalized_reference": "hello world",
                "normalized_hypothesis": "noise",
                "reference_word_count": 2,
                "reference_char_count": 10,
                "word_edits": 2,
                "char_edits": 5,
                "exact_match": False,
                "wer": 1.0,
                "cer": 0.5,
            },
        },
    ]

    summary = summarize_result_rows(rows, exclude_corrupted=True)

    assert summary["total_samples"] == 2
    assert summary["successful_samples"] == 2
    assert summary["aggregate_samples"] == 1
    assert summary["corrupted_samples"] == 1
    assert summary["aggregate_excludes_corrupted"] is True
    assert summary["mean_metrics"]["wer"] == 0.0
    assert summary["mean_metrics"]["total_latency_ms"] == 10.0


def test_summarize_result_rows_keeps_exact_match_rate_independent_from_zero_cer() -> None:
    rows = [
        {
            "success": True,
            "metrics": {"wer": 1.0, "cer": 0.0, "sample_accuracy": 0.0},
            "reference_text": "10001 90210 01803",
            "text": "100019021001803.",
            "quality_support": {
                "normalized_reference": "10001 90210 01803",
                "normalized_hypothesis": "100019021001803",
                "reference_word_count": 3,
                "reference_char_count": 15,
                "word_edits": 3,
                "char_edits": 0,
                "exact_match": False,
                "wer": 1.0,
                "cer": 0.0,
            },
        }
    ]

    summary = summarize_result_rows(rows)

    assert summary["mean_metrics"]["cer"] == 0.0
    assert summary["mean_metrics"]["sample_accuracy"] == 0.0
    assert summary["metric_statistics"]["sample_accuracy"] == {
        "count": 1,
        "aggregator": "rate",
        "numerator": 0,
        "denominator": 1,
        "value": 0.0,
    }
