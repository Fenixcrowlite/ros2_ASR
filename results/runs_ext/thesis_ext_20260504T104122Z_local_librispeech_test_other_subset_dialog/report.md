# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1846153846 | 0.09576642336 | 2119.977291 | 0.357031554 | 70.12079359 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/whisper_local:light | light | 0.3656804734 | 0.2181021898 | 701.7085433 | 0.1744295524 | 48.53317321 | yes |  |
| providers/vosk_local:en_small | en_small | 0.4698224852 | 0.3097810219 | 1921.075184 | 0.220608043 | 42.57209995 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_dialog/plots`
