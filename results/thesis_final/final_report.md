# Final Thesis ASR Benchmark Report

## Thesis Goal

This report summarizes a bachelor thesis prototype for ROS2 ASR integration and experimental comparison of selected commercial and non-commercial ASR systems.

## Tested Providers

Implemented providers: whisper_local, vosk_local, huggingface_local, huggingface_api, azure_cloud, google_cloud, aws_cloud
Smoke-tested providers: aws_cloud, azure_cloud, google_cloud, huggingface_api, huggingface_local, vosk_local, whisper_local
Benchmarked providers: aws_cloud, azure_cloud, google_cloud, huggingface_local, vosk_local, whisper_local
Local providers benchmarked: whisper_local, vosk_local, huggingface_local
Cloud providers benchmarked or attempted: huggingface_api, azure_cloud, google_cloud, aws_cloud

## Cloud Provider Outcomes

| Provider | Credentials Detected | Auth Probe | Benchmark | Safe Failure Reason |
|---|---|---|---|---|
| huggingface_api | no | failure | failure | token |
| azure_cloud | yes | success | success | none |
| google_cloud | yes | success | success | none |
| aws_cloud | yes | success | success | none |

## Skipped Providers

| Provider | Reason |
|---|---|
| huggingface_api | missing_credentials: token |

## Dataset Description

Selected schema-first runs: 12
Dataset used: librispeech_test_clean_subset
Active validated dataset: librispeech_test_clean_subset
Clean source utterances in quality table: 10
Utterance-variant rows in performance and robustness tables: 550
Dataset validation status: passed
Primary benchmark mode: tiered local/cloud comparison

Fast tier run id:
thesis_fast_20260503T225907Z

Balanced tier run id:
thesis_balanced_20260503T232650Z

Accurate tier run id:
thesis_accurate_20260503T225907Z

Cloud matrix run id:
thesis_cloud_20260503T223116Z

Local matrix run id:
thesis_local_20260503T222647Z

The local and cloud matrix runs are supporting evidence for provider coverage and credentialed cloud execution; final provider ranking uses the tiered benchmark artifacts.
Dataset validation report: `reports/datasets/dataset_asset_validation.md`
Credential availability report: `reports/thesis_test/credential_availability.md`

## Hardware And Software Environment

OS: Linux-6.17.0-22-generic-x86_64-with-glibc2.39
Python: 3.12.3
Git branch: main
Git commit: d67aabb3dfb2b8fbdbf459de4377bade9adf6d11

## Methodology

Canonical benchmark artifacts are collected into schema-first run directories under `results/runs/<run_id>/`, then exported into thesis tables under `results/thesis_final/`.
Default thesis evidence validation reads `results/thesis_final/manifest.json` and validates only the final thesis evidence package; historical schema-first runs are excluded unless `--all` is requested.
Synthetic test providers are excluded from final thesis tables.
Quality results are computed from clean source utterances. Noise robustness is reported separately from clean/noisy utterance variants.
Fair comparison is reported by preset tier, not by mixing light, balanced and accurate models in one ranking.

## Fair Preset Tiers

| Tier | Included provider presets |
|---|---|
| fast_or_low_resource | huggingface_local:light, whisper_local:light, google_cloud:light, vosk_local:en_small |
| balanced | huggingface_local:balanced, azure_cloud:standard, aws_cloud:standard, google_cloud:balanced, whisper_local:balanced |
| accurate_or_high_quality | whisper_local:accurate, google_cloud:accurate |

## Failed Preset Attempts

| Tier | Provider | Model | Failed Variants | Sanitized Reason |
|---|---|---:|---:|---|
| accurate_or_high_quality | huggingface_local | accurate | 50 | hf_local_runtime_error: CUDA out of memory during local HuggingFace accurate preset; high-memory preset excluded from metric tables to preserve workstation stability. |

## Canonical Benchmark Artifacts

- `artifacts/benchmark_runs/thesis_accurate_20260503T225907Z`
- `artifacts/benchmark_runs/thesis_balanced_20260503T232650Z`
- `artifacts/benchmark_runs/thesis_cloud_20260503T223116Z`
- `artifacts/benchmark_runs/thesis_fast_20260503T225907Z`
- `artifacts/benchmark_runs/thesis_local_20260503T222647Z`

## Run Completion

| Run | Total Rows | Successful | Failed |
|---|---:|---:|---:|
| thesis_accurate_20260503T225907Z | 150 | 100 | 50 |
| thesis_balanced_20260503T232650Z | 250 | 250 | 0 |
| thesis_cloud_20260503T223116Z | 150 | 150 | 0 |
| thesis_fast_20260503T225907Z | 200 | 199 | 1 |
| thesis_local_20260503T222647Z | 150 | 149 | 1 |

## Metric Definitions

WER/CER/SER measure recognition quality. Final latency and end-to-end RTF measure ROS2/operator-facing performance. `provider_compute_rtf` is secondary and `real_time_factor` is a deprecated compatibility alias.
Primary RTF = `end_to_end_rtf`. `provider_compute_rtf` is secondary. `real_time_factor` is a deprecated alias retained for compatibility.

## Tables Summary

- `provider_comparison.csv`: 7 rows
- `provider_smoke_tests.csv`: 7 rows
- `quality_table.csv`: 11 rows
- `performance_table.csv`: 11 rows
- `resource_table.csv`: 11 rows
- `noise_robustness_table.csv`: 11 rows
- `cost_deployment_table.csv`: 11 rows
- `scenario_scores.csv`: 11 rows

## Main Findings

The generated CSV tables contain the provider-level quality, performance, resource, robustness, cost and scenario suitability values used for thesis interpretation.

## Limitations

The results are indicative and suitable for bachelor-thesis prototype evaluation, but not a large-scale ASR benchmark.
The canonical benchmark contains 52 failed utterance-variant row(s). Completely failed presets are reported as failed attempts and excluded from quality/performance ranking tables.

## Recommendation For ROS2/COCOHRIP

Use local providers for offline ROS2 experiments and cloud providers only when internet access, credentials, latency and cost are acceptable for the laboratory scenario.
