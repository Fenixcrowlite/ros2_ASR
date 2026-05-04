# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_mls_german_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1313131313 | 0.04628647215 | 2015.89727 | 0.1132054752 | 81.57110817 | yes |  |
| providers/vosk_local:en_small | en_small | 1.153535354 | 0.7107427056 | 3958.132468 | 0.1505475697 | 59.76210917 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 0.4437710438 | 0.1916445623 | 771.1906104 | 0.04428232467 | 56.26257538 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_batch/plots`
