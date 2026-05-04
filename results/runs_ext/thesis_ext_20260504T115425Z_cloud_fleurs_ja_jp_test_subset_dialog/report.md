# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 1.342857143 | 0.1393034826 | 4373.992639 | 0.190358349 | 38.80915044 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/azure_cloud:standard | standard | 0.9714285714 | 0.2951907131 | 8538.685023 | 0.2457817695 | 34.89515139 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/aws_cloud:standard | standard | 0.9714285714 | 0.06135986733 | 11098.97383 | 0.6842404882 | 33.49003434 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_dialog/plots`
