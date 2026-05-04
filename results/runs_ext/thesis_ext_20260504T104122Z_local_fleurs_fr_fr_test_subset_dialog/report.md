# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/vosk_local:en_small | en_small | 1.021186441 | 0.776729048 | 3972.38274 | 0.2102577011 | 46.10156438 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/whisper_local:light | light | 1.455932203 | 0.8336859235 | 2632.60063 | 0.1003297508 | 44.29801049 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/huggingface_local:balanced | balanced | 0.4728813559 | 0.2471928397 | 2925.938884 | 0.1974724639 | 43.70993186 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_dialog/plots`
