# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T222647Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3785.664235 | 0.2347758673 | 87.87294869 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 950.450691 | 0.09156301096 | 71.41580156 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2271.356829 | 0.1457393001 | 53.87522121 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T222647Z_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T222647Z_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T222647Z_dialog/summary.csv`
- plots: `results/runs/thesis_local_20260503T222647Z_dialog/plots`
