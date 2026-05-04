# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1885167464 | 0.09680284192 | 1732.851449 | 0.15577174 | 64.74466362 | yes |  |
| providers/whisper_local:light | light | 0.6765550239 | 0.4676731794 | 1375.926175 | 0.06863721042 | 24.75314159 | no | analytics_wer_above_baseline |
| providers/vosk_local:en_small | en_small | 0.6258373206 | 0.4989342806 | 2565.971733 | 0.1190364942 | 23.97884046 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_analytics/plots`
