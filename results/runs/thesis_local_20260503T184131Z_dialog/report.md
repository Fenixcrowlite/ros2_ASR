# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T184131Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3976.012523 | 0.258026219 | 87.69358223 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 949.0913489 | 0.09473022586 | 71.42854939 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2222.424114 | 0.1471882126 | 53.67344931 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T184131Z_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T184131Z_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T184131Z_dialog/summary.csv`
- plots: `results/runs/thesis_local_20260503T184131Z_dialog/plots`
