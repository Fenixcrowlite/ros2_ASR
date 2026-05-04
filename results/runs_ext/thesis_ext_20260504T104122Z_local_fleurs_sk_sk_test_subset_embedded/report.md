# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/vosk_local:en_small | en_small | 1.288461538 | 0.8314814815 | 3067.114477 | 0.2076511213 | 55.78651171 | yes |  |
| providers/whisper_local:light | light | 1.801282051 | 0.8189814815 | 1879.201088 | 0.09218120894 | 55.64347074 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.5602564103 | 0.2136574074 | 2460.141525 | 0.2073037221 | 50.54977677 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_embedded/plots`
