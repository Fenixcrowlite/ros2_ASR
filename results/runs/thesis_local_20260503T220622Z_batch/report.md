# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T220622Z_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3731.230282 | 0.2368794234 | 92.33074982 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 929.3311467 | 0.08901182084 | 81.34298291 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2381.233229 | 0.148918795 | 65.35217447 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T220622Z_batch/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T220622Z_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T220622Z_batch/summary.csv`
- plots: `results/runs/thesis_local_20260503T220622Z_batch/plots`
