# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.202970297 | 0.09391304348 | 2090.7347 | 0.2167790799 | 73.4568887 | yes |  |
| providers/whisper_local:light | light | 0.399009901 | 0.1902608696 | 791.0280489 | 0.08481099227 | 63.35629578 | yes |  |
| providers/vosk_local:en_small | en_small | 1.205940594 | 0.732173913 | 3431.880637 | 0.2419594923 | 57.58218335 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset_embedded/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset_embedded/plots`
