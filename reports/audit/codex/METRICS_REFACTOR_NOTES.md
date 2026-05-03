# Metrics Refactor Notes

## Implemented in this repair

- Re-anchored operator benchmark path on `BenchmarkOrchestrator`
- Re-anchored report generation on canonical `summary.json`
- Preserved flat JSON/CSV only as compatibility export, not as primary metric source

## Semantic rules to keep

- `mean_metrics` is for comparable averages
- `metric_statistics.<metric>.sum` is for totals
- top-level metrics must stay empty for mixed multi-provider runs
- `provider_summaries` is the only valid comparison surface in multi-provider summaries

## Next metric work recommended

1. Add canonical confidence metrics if they are needed for research claims.
2. Add resource metrics only when collection semantics are reproducible across providers.
3. Move `live_sample_eval.py` onto the same summary/export helpers used by benchmark core.
