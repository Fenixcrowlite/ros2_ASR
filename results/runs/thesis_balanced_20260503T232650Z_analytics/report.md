# ASR Thesis Benchmark Summary

Run ID: `thesis_balanced_20260503T232650Z_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3796.141131 | 0.2495673996 | 91.00105849 | no | analytics_wer_above_baseline |
| providers/azure_cloud:standard | standard | 0.02390438247 | 0.01524822695 | 9754.289883 | 0.3430428755 | 87.49597009 | no | analytics_wer_above_baseline |
| providers/aws_cloud:standard | standard | 0.005577689243 | 0.00390070922 | 11535.9706 | 1.614654712 | 85.20671374 | yes |  |
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 3624.154219 | 0.2095655669 | 79.65944814 | no | analytics_wer_above_baseline |
| providers/whisper_local:balanced | balanced | 0.05816733068 | 0.03262411348 | 1619.795614 | 0.1491969518 | 79.10377477 | no | analytics_wer_above_baseline |

## Artifacts

- manifest: `results/runs/thesis_balanced_20260503T232650Z_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_balanced_20260503T232650Z_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_balanced_20260503T232650Z_analytics/summary.csv`
- plots: `results/runs/thesis_balanced_20260503T232650Z_analytics/plots`
