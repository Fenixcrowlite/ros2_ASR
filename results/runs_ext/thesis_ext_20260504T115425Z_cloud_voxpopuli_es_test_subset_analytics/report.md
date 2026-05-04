# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/aws_cloud:standard | standard | 0.07331378299 | 0.05211912944 | 13105.68004 | 1.035344801 | 64.09615827 | yes |  |
| providers/google_cloud:balanced | balanced | 0.1348973607 | 0.09221076747 | 4705.38844 | 0.2363954584 | 62.57188164 | no | analytics_wer_above_baseline |
| providers/azure_cloud:standard | standard | 0.1612903226 | 0.1345933562 | 8391.306283 | 0.3347102443 | 55.08196053 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset_analytics/plots`
