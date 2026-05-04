# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.08333333333 | 0.03125 | 4488.731556 | 0.2883368887 | 74.71383588 | yes |  |
| providers/google_cloud:balanced | balanced | 0.1346153846 | 0.03703703704 | 2568.119269 | 0.1948561354 | 67.66436398 | no | analytics_wer_above_baseline |
| providers/aws_cloud:standard | standard | 0.08974358974 | 0.01388888889 | 9831.718277 | 1.04530683 | 65.56081799 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_analytics/plots`
