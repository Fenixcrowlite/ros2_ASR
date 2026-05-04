# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.08333333333 | 0.03125 | 4488.731556 | 0.2883368887 | 80.70497887 | yes |  |
| providers/google_cloud:balanced | balanced | 0.1346153846 | 0.03703703704 | 2568.119269 | 0.1948561354 | 80.12056251 | yes |  |
| providers/aws_cloud:standard | standard | 0.08974358974 | 0.01388888889 | 9831.718277 | 1.04530683 | 63.3869059 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_batch/plots`
