# Audit Phase 3: Metrics

## Source of truth

- Metric definitions: `asr_metrics.definitions`
- Text normalization / quality support: `asr_metrics.quality`
- Per-sample evaluation: `asr_metrics.engine`
- Aggregate summaries: `asr_metrics.summary`
- Legacy flat record serialization: `asr_metrics.io`

## What is logically correct now

- `wer` and `cer` use normalized reference/hypothesis text.
- Summary WER/CER are corpus-level aggregates, not arithmetic mean of per-sample WER/CER.
- `sample_accuracy` is exact normalized match rate, not a heuristic derived from WER/CER.
- `success_rate` / `failure_rate` are explicit reliability metrics.
- `estimated_cost_usd` has sum semantics in `metric_statistics` and mean semantics in `mean_metrics`.
- streaming-only metrics are kept out of batch-only metric applicability rules.

## Problems found

- old flat report flow was still operator-facing, which made metric semantics dependent on legacy export layout
- streaming metrics historically leaked as zero-valued clutter into batch summaries
- cost interpretation could be confused because top-level `mean_metrics` stores averages while operators often want totals
- repo documentation still mentions confidence/resource metrics more broadly than the current canonical metric registry actually implements

## Repairs made

- `make bench` now originates from canonical benchmark core and then exports compatibility artifacts
- `make report` now consumes canonical summary JSON
- `generate_report.py` understands both legacy flat record lists and canonical summary objects
- benchmark/report path no longer forces operators back into the legacy metric surface

## Remaining metric gaps

- confidence metrics exist in provider result models but are not yet standardized in the canonical benchmark metric registry
- CPU/RAM/GPU metrics are not yet first-class canonical benchmark metrics
- live-sample evaluation still has partially separate reporting logic
