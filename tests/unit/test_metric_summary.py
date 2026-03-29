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
    assert summary["resource_metrics"]["estimated_cost_usd"] == 0.25
    assert summary["metric_statistics"]["estimated_cost_usd"]["sum"] == 0.25
