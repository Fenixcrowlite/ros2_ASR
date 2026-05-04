# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.003984063745 | 0.002659574468 | 7754.313692 | 0.3562504486 | 86.24048656 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/google_cloud:balanced | balanced | 0.01992031873 | 0.01418439716 | 3662.415925 | 0.2430732513 | 72.00422483 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/aws_cloud:standard | standard | 0.003984063745 | 0.002659574468 | 10912.23807 | 1.532856815 | 62.37247384 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset_dialog/plots`
