# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.04289544236 | 0.01875 | 3981.238526 | 0.2162394129 | 75.14848188 | no | analytics_wer_above_baseline |
| providers/aws_cloud:standard | standard | 0.03217158177 | 0.01875 | 11792.8868 | 0.7781566293 | 73.12439426 | yes |  |
| providers/azure_cloud:standard | standard | 0.1581769437 | 0.166875 | 6595.171042 | 0.313686731 | 54.08336538 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset_analytics/plots`
