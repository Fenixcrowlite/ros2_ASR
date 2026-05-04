# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/vosk_local:en_small | en_small | 1.021186441 | 0.776729048 | 3972.38274 | 0.2102577011 | 57.07746178 | yes |  |
| providers/whisper_local:light | light | 1.455932203 | 0.8336859235 | 2632.60063 | 0.1003297508 | 55.95486157 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.4728813559 | 0.2471928397 | 2925.938884 | 0.1974724639 | 49.13167986 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_embedded/plots`
