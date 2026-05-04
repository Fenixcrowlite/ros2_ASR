# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3768.025529 | 0.2568012973 | 88.49633995 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.1227091633 | 0.07180851064 | 946.7832123 | 0.108064403 | 71.42117319 | yes |  |
| providers/vosk_local:en_small | en_small | 0.2525896414 | 0.1867021277 | 2249.921413 | 0.14852826 | 53.35173236 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset_dialog/plots`
