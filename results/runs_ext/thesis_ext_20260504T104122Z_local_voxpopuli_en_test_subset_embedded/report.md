# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1209677419 | 0.04588329337 | 3403.635965 | 0.2668275887 | 79.74711678 | yes |  |
| providers/whisper_local:light | light | 0.3241935484 | 0.1766586731 | 826.0498011 | 0.1068354306 | 63.59798188 | yes |  |
| providers/vosk_local:en_small | en_small | 0.3580645161 | 0.2233413269 | 3533.762256 | 0.192496996 | 55.51966478 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_embedded/plots`
