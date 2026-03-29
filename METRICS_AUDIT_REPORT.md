# Metrics Audit Report

Date: 2026-03-29

## Scope

Audited the metric path end to end:

- metric definitions and naming,
- per-sample collection,
- summary aggregation,
- CSV/JSON artifact schema,
- Markdown report generation,
- gateway result views and web UI presentation,
- historical benchmark artifacts already stored in the repository.

## What was checked

- `asr_metrics.quality`, `plugins`, `engine`, `summary`, `plotting`
- `asr_benchmark_core.executor` and `orchestrator`
- legacy `asr_benchmark.runner` + `asr_metrics.collector`
- `asr_gateway.result_views` and benchmark/results UI pages
- docs and runbooks that describe benchmark outputs
- stored runs under `artifacts/benchmark_runs/*`
- legacy flat export `results/benchmark_results.json`

## Historical artifact findings

Scanned `125` stored benchmark runs under `artifacts/benchmark_runs`.

- `17` cloud runs had `estimated_cost_usd == 0.0` despite cloud execution context.
- `105` batch runs exposed streaming-only metrics in summary output.
- `23` rows had `sample_accuracy == 1.0` while `wer > 0.0`, which proved the old exact-match rule was logically wrong.

Representative conflict:

- hypothesis: `100019021001803.`
- reference: `10001 90210 01803`
- old result: `wer=1.0`, `cer=0.0`, `sample_accuracy=1.0`

That combination is internally inconsistent and was caused by deriving sample accuracy from `cer == 0`.

## Fixes applied

- `sample_accuracy` now means exact normalized text match, not `cer == 0`.
- summary `WER`/`CER` now use corpus aggregation instead of arithmetic mean of per-sample rates.
- streaming-only metrics are filtered out of batch summaries.
- provider preset pricing metadata now propagates into cost estimation.
- summary statistics now expose explicit aggregation mode and numeric `sum`.
- benchmark markdown summary now shows total estimated cost separately from mean per-sample cost.
- per-provider metrics are now exposed as a first-class `provider_summaries` section in summary artifacts.
- for multi-provider runs the mixed top-level metric aggregate is now suppressed instead of being presented as a meaningful result.
- gateway history/detail views now surface metric metadata/statistics and semantically separated groups.
- benchmark/results UI now renders quality, latency, reliability, cost, and streaming sections separately.
- outdated test seed artifacts were updated to match the cleaned metric schema.
- docs were updated so metric meaning matches code and artifacts.

## Current metric semantics

- `wer`, `cer`: corpus-level in summaries/reports; per-sample in raw rows.
- `sample_accuracy`: exact normalized match rate.
- `estimated_cost_usd` in `mean_metrics`: mean estimated cost per sample.
- `metric_statistics.estimated_cost_usd.sum`: total estimated run cost.
- `first_partial_latency_ms`, `finalization_latency_ms`, `partial_count`: streaming-only metrics.

## Validation

- targeted `mypy`: pass
- targeted `pytest` for metric engine, summary aggregation, orchestrator, CLI flows, gateway result views: pass
- historical artifact scan repeated after fixes to document legacy anomalies

## Remaining limitations

- Existing historical artifact files are not rewritten automatically. Re-run affected benchmarks to regenerate clean summaries.
- Google provider presets still do not define explicit per-minute pricing metadata in `configs/providers/google_cloud.yaml`, so cost estimates for that provider remain configuration-dependent rather than guaranteed by the repo defaults.
