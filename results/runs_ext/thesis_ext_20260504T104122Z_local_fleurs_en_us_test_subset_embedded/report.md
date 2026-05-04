# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1885167464 | 0.09680284192 | 1732.851449 | 0.15577174 | 71.82873176 | yes |  |
| providers/whisper_local:light | light | 0.6765550239 | 0.4676731794 | 1375.926175 | 0.06863721042 | 56.22637592 | yes |  |
| providers/vosk_local:en_small | en_small | 0.6258373206 | 0.4989342806 | 2565.971733 | 0.1190364942 | 52.10461849 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_embedded/plots`
