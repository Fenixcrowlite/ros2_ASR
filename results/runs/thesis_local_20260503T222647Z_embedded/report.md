# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T222647Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3785.664235 | 0.2347758673 | 86.93145781 | yes |  |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 950.450691 | 0.09156301096 | 81.78863681 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2271.356829 | 0.1457393001 | 64.71021303 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T222647Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T222647Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T222647Z_embedded/summary.csv`
- plots: `results/runs/thesis_local_20260503T222647Z_embedded/plots`
