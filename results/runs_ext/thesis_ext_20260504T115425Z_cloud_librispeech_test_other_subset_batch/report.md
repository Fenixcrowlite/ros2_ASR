# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.1124260355 | 0.0496350365 | 2575.891956 | 0.3112413371 | 81.40267571 | yes |  |
| providers/azure_cloud:standard | standard | 0.07692307692 | 0.04233576642 | 3960.787995 | 0.3999034609 | 78.58966308 | yes |  |
| providers/aws_cloud:standard | standard | 0.03550295858 | 0.01313868613 | 9571.740072 | 2.473928829 | 61.95610604 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset_batch/plots`
