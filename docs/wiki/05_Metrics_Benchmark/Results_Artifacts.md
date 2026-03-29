# Results Artifacts

Есть два artifact surface:

- core/gateway benchmark: `artifacts/benchmark_runs/<run_id>/...`
- legacy `make bench`: `results/benchmark_results.*` + `results/report.md` + `results/plots/*.png`

## Canonical run folder

Для нового benchmark pipeline ожидаются:

- `manifest/run_manifest.json`
- `metrics/results.json`
- `metrics/results.csv`
- `reports/summary.json`
- `reports/summary.md`

`summary.json` содержит:

- `provider_summaries`
- `mean_metrics`
- `quality_metrics`
- `latency_metrics`
- `reliability_metrics`
- `cost_metrics`
- `streaming_metrics`
- `metric_statistics`
- `metric_metadata`

Важно:

- в multi-provider run top-level metric aggregate намеренно пустой;
- смотреть и сравнивать нужно только `provider_summaries`;
- `mean_metrics.estimated_cost_usd` это mean per sample.
- `metric_statistics.estimated_cost_usd.sum` это total run cost.
- streaming metrics присутствуют только для streaming run.

## Legacy flat outputs

После `make bench` ожидаются:

- `results/benchmark_results.csv`
- `results/benchmark_results.json`
- `results/report.md`
- `results/plots/*.png`

## Связанные

- [[05_Metrics_Benchmark/Quality_Metrics]]
- [[07_Tooling/Makefile_Targets]]
- [[07_Tooling/Scripts/Generate_Report_Script]]
- [[00_Start/Glossary#Artifact]]
