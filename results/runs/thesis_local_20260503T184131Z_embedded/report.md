# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T184131Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3976.012523 | 0.258026219 | 86.7656723 | yes |  |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 949.0913489 | 0.09473022586 | 81.80567663 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2222.424114 | 0.1471882126 | 64.50275687 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T184131Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T184131Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T184131Z_embedded/summary.csv`
- plots: `results/runs/thesis_local_20260503T184131Z_embedded/plots`
