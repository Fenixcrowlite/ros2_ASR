# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_batch`
Scenario: `batch`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1885167464 | 0.09680284192 | 1732.851449 | 0.15577174 | 76.41677801 | no | batch_throughput_below_q25 |
| providers/whisper_local:light | light | 0.6765550239 | 0.4676731794 | 1375.926175 | 0.06863721042 | 54.60273342 | yes |  |
| providers/vosk_local:en_small | en_small | 0.6258373206 | 0.4989342806 | 2565.971733 | 0.1190364942 | 53.06438438 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_batch/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_batch/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_batch/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset_batch/plots`
