# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/vosk_local:en_small | en_small | 1.021186441 | 0.776729048 | 3972.38274 | 0.2102577011 | 61.19875919 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 1.455932203 | 0.8336859235 | 2632.60063 | 0.1003297508 | 54.49688819 | yes |  |
| providers/huggingface_local:balanced | balanced | 0.4728813559 | 0.2471928397 | 2925.938884 | 0.1974724639 | 53.15065212 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset_batch/plots`
