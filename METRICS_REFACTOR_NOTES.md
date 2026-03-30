# Metrics Refactor Notes

## Completed

### Quality support semantics

- `TextQualitySupport` now exposes:
  - `reference_has_content`
  - `hypothesis_has_content`
- Invalid quality references no longer manufacture a denominator from hypothesis length.
- Empty-reference rows therefore stop pretending to carry meaningful WER/CER.

### Validation boundary

- Canonical benchmark path already rejected empty normalized references when quality metrics were enabled.
- The repaired helper now matches that policy instead of keeping a hidden fallback.

### Benchmark metric ownership

- Canonical metric ownership remains:
  - executor prepares `MetricContext`
  - plugin layer computes per-sample metrics
  - summary layer computes corpus/rate aggregates

### Summary semantics repair

- Reliability metrics (`success_rate`, `failure_rate`) now emit explicit rate statistics with:
  - `numerator`
  - `denominator`
  - `value`
- Benchmark summaries now expose `cost_totals` separately from `cost_metrics`.
- `cost_metrics` remains the per-sample aggregate view.
- `cost_totals` now carries the run/provider total cost view.
- Fake `resource_metrics` aggregation was removed.
- `resource_metrics` is now empty unless real resource metrics are actually implemented.

## Explicit Non-Fixes

- Legacy flat `MetricsCollector` was not removed in this pass, but it no longer powers the default `make bench` operator path.
- Resource samplers were not ported into canonical benchmark core.
- Full pipeline latency was not introduced as a new metric because runtime timing boundaries still need formal definition.

## Recommended Next Metric Refactors

1. Introduce canonical metric plugins for:
   - `preprocess_ms`
   - `inference_ms`
   - `postprocess_ms`
2. Add a separate `pipeline_latency_ms` metric for runtime benchmarking.
3. Add optional resource samplers to benchmark core rather than relying on legacy record schema.
4. Define a provider-normalized confidence contract before exposing confidence metrics in benchmark tables.
