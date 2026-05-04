# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 1.342857143 | 0.1393034826 | 4373.992639 | 0.190358349 | 50.56205281 | yes |  |
| providers/azure_cloud:standard | standard | 0.9714285714 | 0.2951907131 | 8538.685023 | 0.2457817695 | 47.03431154 | yes |  |
| providers/aws_cloud:standard | standard | 0.9714285714 | 0.06135986733 | 11098.97383 | 0.6842404882 | 46.83945622 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset_embedded/plots`
