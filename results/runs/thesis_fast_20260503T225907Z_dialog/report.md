# ASR Thesis Benchmark Summary

Run ID: `thesis_fast_20260503T225907Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:light | light | 0.1450199203 | 0.1007092199 | 1394.960945 | 0.07624736666 | 79.36245287 | no | dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 926.2279926 | 0.0923386079 | 71.30932261 | yes |  |
| providers/google_cloud:light | light | 0.1195219124 | 0.08173758865 | 4526.148678 | 0.2466073437 | 64.74864323 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2422.736262 | 0.1533455158 | 53.21509576 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_fast_20260503T225907Z_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_fast_20260503T225907Z_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_fast_20260503T225907Z_dialog/summary.csv`
- plots: `results/runs/thesis_fast_20260503T225907Z_dialog/plots`
