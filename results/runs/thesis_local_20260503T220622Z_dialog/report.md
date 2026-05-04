# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T220622Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3731.230282 | 0.2368794234 | 88.68510243 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 929.3311467 | 0.08901182084 | 71.43479141 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2381.233229 | 0.148918795 | 53.75318013 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T220622Z_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T220622Z_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T220622Z_dialog/summary.csv`
- plots: `results/runs/thesis_local_20260503T220622Z_dialog/plots`
