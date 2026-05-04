# ASR Thesis Benchmark Summary

Run ID: `thesis_fast_20260503T225907Z_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:light | light | 0.1450199203 | 0.1007092199 | 1394.960945 | 0.07624736666 | 68.40925142 | no | analytics_wer_above_baseline |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 926.2279926 | 0.0923386079 | 67.98516648 | no | analytics_wer_above_baseline |
| providers/google_cloud:light | light | 0.1195219124 | 0.08173758865 | 4526.148678 | 0.2466073437 | 67.68723168 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2422.736262 | 0.1533455158 | 42.60720574 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_fast_20260503T225907Z_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_fast_20260503T225907Z_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_fast_20260503T225907Z_analytics/summary.csv`
- plots: `results/runs/thesis_fast_20260503T225907Z_analytics/plots`
