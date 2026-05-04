# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.09069767442 | 0.04605263158 | 1445.5573 | 0.2833462743 | 82.30033369 | no | dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.2662790698 | 0.1560526316 | 531.1420933 | 0.1161560689 | 56.08232832 | yes |  |
| providers/vosk_local:en_small | en_small | 0.3337209302 | 0.2397368421 | 1668.092544 | 0.2160768415 | 45.37345452 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset_dialog/plots`
