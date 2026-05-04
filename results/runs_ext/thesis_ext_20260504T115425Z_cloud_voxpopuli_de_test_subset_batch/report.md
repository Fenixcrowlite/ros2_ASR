# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:balanced | balanced | 0.1485148515 | 0.06869565217 | 4069.691538 | 0.3063184944 | 73.69686157 | yes |  |
| providers/azure_cloud:standard | standard | 0.2772277228 | 0.2069565217 | 4338.020354 | 0.3179169021 | 62.73469487 | yes |  |
| providers/aws_cloud:standard | standard | 0.08415841584 | 0.04782608696 | 11858.3394 | 1.421042633 | 59.52333524 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset_batch/plots`
