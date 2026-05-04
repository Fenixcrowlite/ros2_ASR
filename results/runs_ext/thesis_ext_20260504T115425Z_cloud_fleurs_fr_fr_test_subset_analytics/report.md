# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.05508474576 | 0.016273393 | 5516.775882 | 0.2805478901 | 76.13350208 | no | analytics_wer_above_baseline |
| providers/google_cloud:balanced | balanced | 0.08474576271 | 0.0211554109 | 4511.131371 | 0.3120025492 | 72.53593331 | no | analytics_wer_above_baseline |
| providers/aws_cloud:standard | standard | 0.04237288136 | 0.0146460537 | 11091.38533 | 1.115812811 | 71.6867202 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_analytics/plots`
