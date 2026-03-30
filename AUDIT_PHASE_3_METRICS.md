# Audit Phase 3 Metrics

## Canonical Metric Surface

Implemented in the canonical benchmark path:

- `wer`
- `cer`
- `sample_accuracy`
- `total_latency_ms`
- `per_utterance_latency_ms`
- `real_time_factor`
- `estimated_cost_usd`
- `success_rate`
- `failure_rate`
- `first_partial_latency_ms`
- `finalization_latency_ms`
- `partial_count`

Primary code paths:

- metric plugins: `ros2_ws/src/asr_metrics/asr_metrics/plugins.py`
- definitions/metadata: `ros2_ws/src/asr_metrics/asr_metrics/definitions.py`
- corpus aggregation: `ros2_ws/src/asr_metrics/asr_metrics/summary.py`
- sample execution context: `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py`

## Key Findings

### 1. Quality metrics are centralized in the canonical path

This is good:

- normalization is centralized in `asr_metrics.quality`
- benchmark core passes `TextQualitySupport` into metric evaluation
- summary layer aggregates WER/CER at corpus level instead of averaging per-sample rates blindly

### 2. Empty-reference semantics were previously misleading

Before repair:

- `text_quality_support` silently reused hypothesis length as denominator when normalized reference was empty
- that created pseudo-WER/CER values for data without valid ground truth

After repair:

- `TextQualitySupport` explicitly marks `reference_has_content`
- `reference_word_count` / `reference_char_count` remain zero when no valid reference exists
- exact match is no longer claimed for empty-reference rows
- canonical benchmark path already rejects such rows when quality metrics are enabled

### 3. Latency semantics are only partially honest

Current canonical meaning of `total_latency_ms`:

- provider-result latency returned by the adapter/backend path
- useful for provider comparison
- not a full capture-to-final runtime session latency metric

Not yet modeled separately:

- microphone/file replay delay
- VAD buffering latency
- orchestrator control-plane latency
- end-to-end UI-visible latency

### 4. Resource metrics are legacy-only

`cpu_percent`, `ram_mb`, `gpu_util_percent`, `gpu_mem_mb` exist only in the old flat `MetricsCollector` / `BenchmarkRecord` flow.

That means:

- canonical benchmark core does not currently expose resource metrics
- the repository should not claim resource metrics as part of the canonical benchmark baseline
- summary payloads should not fake a `resource_metrics` block by stuffing latency/cost/streaming metrics into it

### 5. Summary semantics had internal inconsistencies

Before repair:

- `success_rate` / `failure_rate` were summarized as generic scalar series instead of explicit rates
- total cost existed only implicitly inside `metric_statistics[*].sum`
- `resource_metrics` falsely mixed latency, streaming, and cost metrics

After repair:

- reliability summary statistics now expose `numerator` / `denominator` / `value`
- benchmark summaries expose `cost_totals`
- `resource_metrics` is empty unless real resource metrics exist

### 6. Noise robustness is represented structurally, not as a scalar metric

Current honest behavior:

- scenario/noise slicing exists
- per-noise summaries exist in benchmark summary

Missing:

- a standalone `noise_robustness_score`
- a formal cross-scenario robustness aggregator

### 7. Confidence and language-detection metrics are not benchmark metrics yet

Even though provider results can carry confidence / detected language signals:

- no canonical benchmark metric plugins exist for them
- no cross-provider normalization policy exists for comparing them

### 8. Default local reporting is now anchored to canonical metric summaries

After repair:

- `make bench` produces canonical `summary.json` first
- compatibility flat exports are derived from canonical benchmark rows
- `make report` reads `results/latest_benchmark_summary.json` instead of treating `results/benchmark_results.json` as the primary truth source

## Repairs Performed

1. Removed misleading empty-reference fallback behavior from `TextQualitySupport` semantics.
2. Repaired reliability summary semantics so rate metrics are reported as rates, not pseudo-distributions.
3. Added explicit `cost_totals` into benchmark summaries.
4. Removed fake `resource_metrics` aggregation behavior.
5. Added regression coverage for the repaired metric summary contracts.
6. Shifted the default report path to canonical benchmark summary artifacts while keeping compatibility exports.

## Remaining Gaps

- no canonical standalone preprocess/inference/postprocess metric plugins
- no full pipeline latency metric
- no throughput metric
- no canonical resource metric plugin set
- no normalized confidence benchmark contract
- no normalized language-detection quality benchmark contract

See also:

- `AUDIT_METRICS_MATRIX.csv`
- `METRICS_REFACTOR_NOTES.md`
