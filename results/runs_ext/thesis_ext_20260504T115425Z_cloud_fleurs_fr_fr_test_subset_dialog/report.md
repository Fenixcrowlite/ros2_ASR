# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.05508474576 | 0.016273393 | 5516.775882 | 0.2805478901 | 66.75275955 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/google_cloud:balanced | balanced | 0.08474576271 | 0.0211554109 | 4511.131371 | 0.3120025492 | 62.5874954 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/aws_cloud:standard | standard | 0.04237288136 | 0.0146460537 | 11091.38533 | 1.115812811 | 51.68466743 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset_dialog/plots`
