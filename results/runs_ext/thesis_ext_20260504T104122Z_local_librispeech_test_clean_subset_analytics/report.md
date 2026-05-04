# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3768.025529 | 0.2568012973 | 91.09495727 | yes |  |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 946.7832123 | 0.108064403 | 68.00394977 | no | analytics_wer_above_baseline |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2249.921413 | 0.14852826 | 42.86488872 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_analytics/plots`
