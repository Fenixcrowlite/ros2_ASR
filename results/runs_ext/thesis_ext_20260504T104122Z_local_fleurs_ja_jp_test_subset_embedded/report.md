# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/whisper_local:light | light | 1.16 | 0.6281923715 | 2268.050199 | 0.06045670349 | 63.31695753 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.9714285714 | 0.176119403 | 4738.250829 | 0.1535639618 | 58.6639358 | yes |  |
| providers/vosk_local:en_small | en_small | 7.097142857 | 1.670978441 | 4850.508064 | 0.1722459776 | 54.47615781 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset_embedded/plots`
