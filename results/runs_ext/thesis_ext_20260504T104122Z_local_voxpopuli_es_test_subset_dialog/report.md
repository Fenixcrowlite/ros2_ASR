# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1554252199 | 0.1016036655 | 4096.398828 | 0.1731814828 | 73.83883916 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.517888563 | 0.3049255441 | 2020.631181 | 0.07476419997 | 43.78478917 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/vosk_local:en_small | en_small | 1.304398827 | 0.8040091638 | 5286.582259 | 0.2673832213 | 39.14323298 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_dialog/plots`
