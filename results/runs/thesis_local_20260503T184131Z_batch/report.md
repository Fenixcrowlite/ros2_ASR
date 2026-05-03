# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T184131Z_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3976.012523 | 0.258026219 | 91.97208645 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 949.0913489 | 0.09473022586 | 81.33361988 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2222.424114 | 0.1471882126 | 65.31890638 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T184131Z_batch/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T184131Z_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T184131Z_batch/summary.csv`
- plots: `results/runs/thesis_local_20260503T184131Z_batch/plots`
