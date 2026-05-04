# ASR Thesis Benchmark Summary

Run ID: `thesis_balanced_20260503T232650Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3796.141131 | 0.2495673996 | 87.20815442 | yes |  |
| providers/whisper_local:balanced | balanced | 0.05816733068 | 0.03262411348 | 1619.795614 | 0.1491969518 | 86.29410138 | yes |  |
| providers/azure_cloud:standard | standard | 0.02390438247 | 0.01524822695 | 9754.289883 | 0.3430428755 | 83.64200446 | yes |  |
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 3624.154219 | 0.2095655669 | 82.27099657 | yes |  |
| providers/aws_cloud:standard | standard | 0.005577689243 | 0.00390070922 | 11535.9706 | 1.614654712 | 66.18386549 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_balanced_20260503T232650Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_balanced_20260503T232650Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_balanced_20260503T232650Z_embedded/summary.csv`
- plots: `results/runs/thesis_balanced_20260503T232650Z_embedded/plots`
