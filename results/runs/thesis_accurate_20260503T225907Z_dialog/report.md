# ASR Thesis Benchmark Summary

Run ID: `thesis_accurate_20260503T225907Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/google_cloud:accurate | accurate | 0.07330677291 | 0.04237588652 | 3459.973583 | 0.1930650076 | 70.91777677 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/whisper_local:accurate | accurate | 0.02709163347 | 0.01560283688 | 3494.021452 | 0.3720004931 | 69.30213074 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/huggingface_local:accurate | accurate | 1 | 1 | 337.5400628 | 1.124251842 | 52.2947107 | no | dialog_confidence_unavailable |

## Artifacts

- manifest: `results/runs/thesis_accurate_20260503T225907Z_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_accurate_20260503T225907Z_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_accurate_20260503T225907Z_dialog/summary.csv`
- plots: `results/runs/thesis_accurate_20260503T225907Z_dialog/plots`
