# Benchmarking Methodology

## Metric surfaces

The repository currently has two benchmark artifact flows:

- Core/gateway benchmark flow writes canonical run folders under `artifacts/benchmark_runs/<run_id>/...`.
- Legacy `make bench` flow writes flat artifacts under `results/benchmark_results.json`, `results/benchmark_results.csv`, `results/report.md`, and `results/plots/`.

Both flows now use the same normalized text-quality baseline for WER/CER plots and reports.

## Metric semantics

- `wer`: corpus-level word error rate in summaries and reports. Raw result rows still store per-sample WER.
- `cer`: corpus-level character error rate in summaries and reports, computed after normalization with spaces removed.
- `sample_accuracy`: share of samples whose normalized reference and hypothesis match exactly. It is not derived from `cer == 0`.
- `total_latency_ms`: end-to-end latency per sample.
- `per_utterance_latency_ms`: backward-compatible alias of total latency for older dashboards.
- `real_time_factor`: processing time divided by audio duration.
- `success_rate` / `failure_rate`: sample-level completion rates.
- `estimated_cost_usd`: per-sample estimate based on configured provider preset pricing metadata or legacy benchmark pricing tables.
- `first_partial_latency_ms`, `finalization_latency_ms`, `partial_count`: streaming-only metrics. They must not appear in batch summaries.

## Aggregation rules

- Quality summaries use corpus aggregation, not arithmetic mean of per-sample WER/CER.
- Scalar timing/resource/cost metrics use arithmetic mean in `mean_metrics`.
- Detailed summary stats live in `metric_statistics`.
- For additive interpretation, use `metric_statistics.<metric>.sum`.
  Example: `metric_statistics.estimated_cost_usd.sum` is total estimated run cost, while `mean_metrics.estimated_cost_usd` is mean estimated cost per sample.
- In multi-provider runs the mixed top-level metric aggregate is intentionally suppressed.
  `provider_summaries` becomes the only metric surface for provider comparison.

## Output artifacts

Core/gateway benchmark run:

- `artifacts/benchmark_runs/<run_id>/manifest/run_manifest.json`
- `artifacts/benchmark_runs/<run_id>/metrics/results.json`
- `artifacts/benchmark_runs/<run_id>/metrics/results.csv`
- `artifacts/benchmark_runs/<run_id>/reports/summary.json`
- `artifacts/benchmark_runs/<run_id>/reports/summary.md`

Legacy `make bench` run:

- `results/benchmark_results.json`
- `results/benchmark_results.csv`
- `results/report.md`
- `results/plots/*.png`

`summary.json` contains grouped views such as:

- `provider_summaries`
- `quality_metrics`
- `latency_metrics`
- `reliability_metrics`
- `cost_metrics`
- `streaming_metrics`
- `metric_statistics`
- `metric_metadata`

## Historical artifact caveat

Existing benchmark folders created before the 2026-03 metrics audit may contain:

- batch summaries polluted with zero-valued streaming metrics,
- cloud runs with zero cost despite configured preset pricing,
- `sample_accuracy=1.0` rows that were not exact normalized matches.

Those artifacts are preserved for traceability. Re-run the affected benchmarks to regenerate clean summaries.

For multi-provider runs, the primary and only metric analysis surface is
`provider_summaries`. Top-level metric groups are intentionally empty there so the
UI/export layer cannot silently compare providers through a mixed aggregate.
