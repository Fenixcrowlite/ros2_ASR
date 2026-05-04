# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T222647Z_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3785.664235 | 0.2347758673 | 90.93796449 | yes |  |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 950.450691 | 0.09156301096 | 68.00693293 | no | analytics_wer_above_baseline |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2271.356829 | 0.1457393001 | 42.98709763 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T222647Z_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T222647Z_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T222647Z_analytics/summary.csv`
- plots: `results/runs/thesis_local_20260503T222647Z_analytics/plots`
