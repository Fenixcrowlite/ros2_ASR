# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.07744107744 | 0.02055702918 | 5468.144632 | 0.2371128091 | 59.57468357 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/aws_cloud:standard | standard | 0.03367003367 | 0.009283819629 | 10853.11743 | 0.5954576107 | 57.76185905 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/azure_cloud:standard | standard | 0.5589225589 | 0.5311671088 | 4776.458588 | 0.149533893 | 38.75948361 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_dialog/plots`
