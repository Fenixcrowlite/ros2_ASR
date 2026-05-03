# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T181036Z_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03921568627 | 0.03348017621 | 36418.4825 | 2.038875806 | 80.66007117 | yes |  |
| providers/whisper_local:light | light | 0.1490196078 | 0.1066079295 | 3991.561854 | 0.2668223508 | 61.89037695 | no | analytics_wer_above_baseline |
| providers/vosk_local:en_small | en_small | 0.2784313725 | 0.2352422907 | 2183.814627 | 0.1772177197 | 35.63982109 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T181036Z_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T181036Z_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T181036Z_analytics/summary.csv`
- plots: `results/runs/thesis_local_20260503T181036Z_analytics/plots`
