# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.08333333333 | 0.03125 | 4488.731556 | 0.2883368887 | 63.53518206 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/google_cloud:balanced | balanced | 0.1346153846 | 0.03703703704 | 2568.119269 | 0.1948561354 | 63.39245544 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/aws_cloud:standard | standard | 0.08974358974 | 0.01388888889 | 9831.718277 | 1.04530683 | 48.74679814 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset_dialog/plots`
