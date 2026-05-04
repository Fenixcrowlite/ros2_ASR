# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.09677419355 | 0.03916866507 | 4503.729254 | 0.2520508434 | 81.48448775 | yes |  |
| providers/azure_cloud:standard | standard | 0.07258064516 | 0.03117505995 | 8269.714014 | 0.4124367307 | 74.61174362 | yes |  |
| providers/aws_cloud:standard | standard | 0.03629032258 | 0.02318145484 | 10839.22924 | 1.912593903 | 66.3554474 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset_batch/plots`
