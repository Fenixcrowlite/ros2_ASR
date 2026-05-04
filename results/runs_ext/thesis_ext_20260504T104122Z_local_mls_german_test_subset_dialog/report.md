# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_mls_german_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1313131313 | 0.04628647215 | 2015.89727 | 0.1132054752 | 74.30982504 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.4437710438 | 0.1916445623 | 771.1906104 | 0.04428232467 | 45.89524807 | yes |  |
| providers/vosk_local:en_small | en_small | 1.153535354 | 0.7107427056 | 3958.132468 | 0.1505475697 | 42.55828036 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_mls_german_test_subset_dialog/plots`
