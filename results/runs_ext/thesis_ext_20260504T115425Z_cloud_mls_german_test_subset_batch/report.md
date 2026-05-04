# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.07744107744 | 0.02055702918 | 5468.144632 | 0.2371128091 | 80.90401049 | yes |  |
| providers/aws_cloud:standard | standard | 0.03367003367 | 0.009283819629 | 10853.11743 | 0.5954576107 | 71.86640516 | no | batch_throughput_below_q25 |
| providers/azure_cloud:standard | standard | 0.5589225589 | 0.5311671088 | 4776.458588 | 0.149533893 | 56.40283709 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_mls_german_test_subset_batch/plots`
