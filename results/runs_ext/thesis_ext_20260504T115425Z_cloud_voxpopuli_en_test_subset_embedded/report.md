# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.09677419355 | 0.03916866507 | 4503.729254 | 0.2520508434 | 72.97950718 | yes |  |
| providers/azure_cloud:standard | standard | 0.07258064516 | 0.03117505995 | 8269.714014 | 0.4124367307 | 69.24572424 | yes |  |
| providers/aws_cloud:standard | standard | 0.03629032258 | 0.02318145484 | 10839.22924 | 1.912593903 | 60.11080144 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_embedded/plots`
