# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_mls_spanish_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.09865951743 | 0.049875 | 2437.596426 | 0.1511926551 | 78.82744975 | yes |  |
| providers/whisper_local:light | light | 0.2932975871 | 0.131625 | 802.6226671 | 0.05499522982 | 67.19638565 | yes |  |
| providers/vosk_local:en_small | en_small | 1.250938338 | 0.83725 | 3826.51058 | 0.2016319737 | 50.92728437 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_mls_spanish_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_mls_spanish_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_mls_spanish_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_mls_spanish_test_subset_embedded/plots`
