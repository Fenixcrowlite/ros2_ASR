# ASR Thesis Benchmark Summary

Run ID: `thesis_balanced_20260503T225907Z_analytics`
Scenario: `analytics`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3880.533586 | 0.234602608 | 90.96068679 | yes |  |
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 4018.627209 | 0.2054183042 | 79.78867238 | yes |  |
| providers/whisper_local:balanced | balanced | 0.05816733068 | 0.03262411348 | 1560.87592 | 0.1476012791 | 78.64338576 | yes |  |
| providers/azure_cloud:standard | standard | 0.1896414343 | 0.1606382979 | 9765.672966 | 0.3462891841 | 64.38604417 | yes |  |
| providers/aws_cloud:standard | standard | 0.2438247012 | 0.2533687943 | 12776.92449 | 1.506339604 | 54.86970641 | yes |  |

## Artifacts

- manifest: `results/runs/thesis_balanced_20260503T225907Z_analytics/manifest.json`
- utterance metrics: `results/runs/thesis_balanced_20260503T225907Z_analytics/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_balanced_20260503T225907Z_analytics/summary.csv`
- plots: `results/runs/thesis_balanced_20260503T225907Z_analytics/plots`
