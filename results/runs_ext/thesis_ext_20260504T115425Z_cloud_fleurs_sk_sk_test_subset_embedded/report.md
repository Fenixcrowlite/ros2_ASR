# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.1346153846 | 0.03703703704 | 2568.119269 | 0.1948561354 | 74.34313365 | yes |  |
| providers/azure_cloud:standard | standard | 0.08333333333 | 0.03125 | 4488.731556 | 0.2883368887 | 74.30633144 | yes |  |
| providers/aws_cloud:standard | standard | 0.08974358974 | 0.01388888889 | 9831.718277 | 1.04530683 | 60.89808507 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_embedded/plots`
