# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T181036Z_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/whisper_local:light | light | 0.1490196078 | 0.1066079295 | 3991.561854 | 0.2668223508 | 67.0541147 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/huggingface_local:balanced | balanced | 0.03921568627 | 0.03348017621 | 36418.4825 | 2.038875806 | 65.49246126 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/vosk_local:en_small | en_small | 0.2784313725 | 0.2352422907 | 2183.814627 | 0.1772177197 | 47.56531533 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_dialog/manifest.json`
- utterance metrics: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_dialog/utterance_metrics.csv`
- summary CSV: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_dialog/summary.csv`
- plots: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_dialog/plots`
