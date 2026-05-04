# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1209677419 | 0.04588329337 | 3403.635965 | 0.2668275887 | 79.41628966 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.3241935484 | 0.1766586731 | 826.0498011 | 0.1068354306 | 52.34230572 | yes |  |
| providers/vosk_local:en_small | en_small | 0.3580645161 | 0.2233413269 | 3533.762256 | 0.192496996 | 44.53695681 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset_dialog/plots`
