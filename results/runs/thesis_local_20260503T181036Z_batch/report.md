# ASR Thesis Benchmark Summary

Run ID: `thesis_local_20260503T181036Z_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/whisper_local:light | light | 0.1490196078 | 0.1066079295 | 3991.561854 | 0.2668223508 | 77.42918671 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.03921568627 | 0.03348017621 | 36418.4825 | 2.038875806 | 70.94667026 | no | batch_throughput_below_q25 |
| providers/vosk_local:en_small | en_small | 0.2784313725 | 0.2352422907 | 2183.814627 | 0.1772177197 | 60.3614512 | yes |  |

## Artifacts

- manifest: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_batch/manifest.json`
- utterance metrics: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_batch/utterance_metrics.csv`
- summary CSV: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_batch/summary.csv`
- plots: `/home/fenix/Desktop/ros2ws/results/runs/thesis_local_20260503T181036Z_batch/plots`
