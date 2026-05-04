# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/azure_cloud:standard | standard | 0.02325581395 | 0.003947368421 | 2150.876174 | 0.3364595348 | 83.74213337 | no | analytics_wer_above_baseline |
| providers/google_cloud:balanced | balanced | 0.02906976744 | 0.006578947368 | 2154.858327 | 0.3022297647 | 80.34736758 | no | analytics_wer_above_baseline |
| providers/aws_cloud:standard | standard | 0.01744186047 | 0.001315789474 | 9668.028013 | 2.116308277 | 77.27681811 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset_analytics/plots`
