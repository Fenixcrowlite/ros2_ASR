# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.1148325359 | 0.0674955595 | 5517.97309 | 0.2664961545 | 69.46622582 | yes |  |
| providers/google_cloud:balanced | balanced | 0.1339712919 | 0.05861456483 | 12895.28869 | 0.4396565494 | 67.7761134 | yes |  |
| providers/aws_cloud:standard | standard | 0.09090909091 | 0.03818827709 | 9643.036181 | 0.9950664356 | 60.83460401 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset_embedded/plots`
