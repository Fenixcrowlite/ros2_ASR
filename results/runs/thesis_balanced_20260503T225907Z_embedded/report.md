# ASR Thesis Benchmark Summary

Run ID: `thesis_balanced_20260503T225907Z_embedded`
Scenario: `embedded`
Normalization: `normalized-v1`

## Model Ranking

| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |
|---|---|---:|---:|---:|---:|---:|---|---|
| providers/huggingface_local:balanced | balanced | 0.03426294821 | 0.01985815603 | 3880.533586 | 0.234602608 | 87.11586744 | yes |  |
| providers/whisper_local:balanced | balanced | 0.05816733068 | 0.03262411348 | 1560.87592 | 0.1476012791 | 84.78234658 | yes |  |
| providers/google_cloud:balanced | balanced | 0.05418326693 | 0.03173758865 | 4018.627209 | 0.2054183042 | 82.98051542 | yes |  |
| providers/azure_cloud:standard | standard | 0.1896414343 | 0.1606382979 | 9765.672966 | 0.3462891841 | 71.68709364 | yes |  |
| providers/aws_cloud:standard | standard | 0.2438247012 | 0.2533687943 | 12776.92449 | 1.506339604 | 48.12548954 | no | embedded_rtf_gt_1 |

## Artifacts

- manifest: `results/runs/thesis_balanced_20260503T225907Z_embedded/manifest.json`
- utterance metrics: `results/runs/thesis_balanced_20260503T225907Z_embedded/utterance_metrics.csv`
- summary CSV: `results/runs/thesis_balanced_20260503T225907Z_embedded/summary.csv`
- plots: `results/runs/thesis_balanced_20260503T225907Z_embedded/plots`
