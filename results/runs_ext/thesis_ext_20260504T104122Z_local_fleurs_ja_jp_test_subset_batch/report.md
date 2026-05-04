# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.9714285714 | 0.176119403 | 4738.250829 | 0.1535639618 | 64.11497562 | yes |  |
| providers/whisper_local:light | light | 1.16 | 0.6281923715 | 2268.050199 | 0.06045670349 | 62.31391335 | yes |  |
| providers/vosk_local:en_small | en_small | 7.097142857 | 1.670978441 | 4850.508064 | 0.1722459776 | 60.22549396 | no | batch_throughput_below_q25 |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_batch/plots`
