# ASR Thesis Benchmark Summary

Run ID: `thesis_cloud_20260503T223116Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.02390438247 | 0.01524822695 | 9715.550494 | 0.3404585474 | 85.98694489 | yes |  |
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 3809.037204 | 0.215368056 | 83.84194943 | yes |  |
| providers/aws_cloud:standard | standard | 0.005577689243 | 0.00390070922 | 11691.2084 | 1.614649067 | 68.30728495 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_cloud_20260503T223116Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_cloud_20260503T223116Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_cloud_20260503T223116Z_embedded/summary.csv`
- plots: `results/runs/thesis_cloud_20260503T223116Z_embedded/plots`
