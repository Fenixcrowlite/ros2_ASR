# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T181036Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/whisper_local:light | light | 0.1490196078 | 0.1066079295 | 3991.561854 | 0.2668223508 | 77.55073928 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.03921568627 | 0.03348017621 | 36418.4825 | 2.038875806 | 68.11272574 | no | embedded_rtf_gt_1 |
| providers/vosk_local:en_small | en_small | 0.2784313725 | 0.2352422907 | 2183.814627 | 0.1772177197 | 58.43814106 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_local_20260503T181036Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_local_20260503T181036Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_local_20260503T181036Z_embedded/summary.csv`
- plots: `results/runs/thesis_local_20260503T181036Z_embedded/plots`
