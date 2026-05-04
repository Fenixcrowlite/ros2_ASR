# ASR Thesis Benchmark Summary

Run ID: `thesis_cloud_20260503T223116Z_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 3809.037204 | 0.215368056 | 87.41298071 | yes |  |
| providers/azure_cloud:standard | standard | 0.02390438247 | 0.01524822695 | 9715.550494 | 0.3404585474 | 86.72790452 | yes |  |
| providers/aws_cloud:standard | standard | 0.005577689243 | 0.00390070922 | 11691.2084 | 1.614649067 | 73.33110101 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_cloud_20260503T223116Z_batch/manifest.json`
- utterance metrics: `results/runs/thesis_cloud_20260503T223116Z_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_cloud_20260503T223116Z_batch/summary.csv`
- plots: `results/runs/thesis_cloud_20260503T223116Z_batch/plots`
