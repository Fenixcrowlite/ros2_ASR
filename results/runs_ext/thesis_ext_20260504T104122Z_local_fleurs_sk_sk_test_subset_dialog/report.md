# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_dialog`
Scenario: `dialog`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.5602564103 | 0.2136574074 | 2460.141525 | 0.2073037221 | 45.71162861 | no | dialog_final_latency_p95_gt_1500_ms,dialog_confidence_unavailable |
| providers/vosk_local:en_small | en_small | 1.288461538 | 0.8314814815 | 3067.114477 | 0.2076511213 | 44.91324922 | no | dialog_final_latency_p95_gt_1500_ms |
| providers/whisper_local:light | light | 1.801282051 | 0.8189814815 | 1879.201088 | 0.09218120894 | 44.0038729 | no | dialog_final_latency_p95_gt_1500_ms |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_dialog/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_dialog/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_dialog/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset_dialog/plots`
