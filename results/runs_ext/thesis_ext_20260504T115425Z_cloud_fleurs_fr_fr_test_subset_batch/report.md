# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.05508474576 | 0.016273393 | 5516.775882 | 0.2805478901 | 82.25415509 | yes |  |
| providers/google_cloud:balanced | balanced | 0.08474576271 | 0.0211554109 | 4511.131371 | 0.3120025492 | 79.20203505 | yes |  |
| providers/aws_cloud:standard | standard | 0.04237288136 | 0.0146460537 | 11091.38533 | 1.115812811 | 66.54606682 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_batch/plots`
