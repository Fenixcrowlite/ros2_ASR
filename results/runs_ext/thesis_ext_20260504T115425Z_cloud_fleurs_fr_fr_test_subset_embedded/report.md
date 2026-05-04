# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.05508474576 | 0.016273393 | 5516.775882 | 0.2805478901 | 77.71168325 | yes |  |
| providers/google_cloud:balanced | balanced | 0.08474576271 | 0.0211554109 | 4511.131371 | 0.3120025492 | 73.54052176 | yes |  |
| providers/aws_cloud:standard | standard | 0.04237288136 | 0.0146460537 | 11091.38533 | 1.115812811 | 63.57278241 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_embedded/plots`
