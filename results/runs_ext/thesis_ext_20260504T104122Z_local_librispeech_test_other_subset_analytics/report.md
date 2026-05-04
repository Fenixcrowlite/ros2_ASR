# ASR Thesis Benchmark Summary

Run ID: `thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.1846153846 | 0.09576642336 | 2119.977291 | 0.357031554 | 61.33791558 | yes |  |
| providers/whisper_local:light | light | 0.3656804734 | 0.2181021898 | 701.7085433 | 0.1744295524 | 30.86277002 | no | analytics_wer_above_baseline |
| providers/vosk_local:en_small | en_small | 0.4698224852 | 0.3097810219 | 1921.075184 | 0.220608043 | 24.34128225 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_analytics/summary.csv`
- plots: `results/runs/thesis_ext_20260504T104122Z_local_librispeech_test_other_subset_analytics/plots`
