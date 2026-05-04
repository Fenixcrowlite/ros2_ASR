# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.9714285714 | 0.176119403 | 4738.250829 | 0.1535639618 | 48.06016526 | yes |  |
| providers/vosk_local:en_small | en_small | 7.097142857 | 1.670978441 | 4850.508064 | 0.1722459776 | 42.55350116 | no | analytics_wer_above_baseline |
| providers/whisper_local:light | light | 1.16 | 0.6281923715 | 2268.050199 | 0.06045670349 | 40.74637893 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_analytics/plots`
