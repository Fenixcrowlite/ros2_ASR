# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1554252199 | 0.1016036655 | 4096.398828 | 0.1731814828 | 80.48279756 | yes |  |
| providers/vosk_local:en_small | en_small | 1.304398827 | 0.8040091638 | 5286.582259 | 0.2673832213 | 57.8152635 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 0.517888563 | 0.3049255441 | 2020.631181 | 0.07476419997 | 54.28290193 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset_batch/plots`
