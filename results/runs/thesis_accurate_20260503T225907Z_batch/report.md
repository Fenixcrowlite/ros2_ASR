# ASR Thesis Benchmark Summary

Run ID: `thesis_accurate_20260503T225907Z_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/whisper_local:accurate | accurate | 0.02709163347 | 0.01560283688 | 3494.021452 | 0.3720004931 | 84.46775809 | yes |  |
| providers/google_cloud:accurate | accurate | 0.07330677291 | 0.04237588652 | 3459.973583 | 0.1930650076 | 83.73028509 | yes |  |
| providers/huggingface_local:accurate | accurate | 1 | 1 | 337.5400628 | 1.124251842 | 54.47733883 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_accurate_20260503T225907Z_batch/manifest.json`
- utterance metrics: `results/runs/thesis_accurate_20260503T225907Z_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_accurate_20260503T225907Z_batch/summary.csv`
- plots: `results/runs/thesis_accurate_20260503T225907Z_batch/plots`
