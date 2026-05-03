# Final Thesis ASR Benchmark Report

## Thesis Goal

This report summarizes a bachelor thesis prototype for ROS2 ASR integration and experimental comparison of selected commercial and non-commercial ASR systems.

## Tested Providers

Implemented providers: whisper_local, vosk_local, huggingface_local, huggingface_api, azure_cloud, google_cloud, aws_cloud
Smoke-tested providers: aws_cloud, azure_cloud, google_cloud, huggingface_api, huggingface_local, vosk_local, whisper_local
Benchmarked providers: huggingface_local, vosk_local, whisper_local

## Skipped Providers

| Provider | Reason |
|---|---|
| huggingface_api | missing_credentials: HF_TOKEN |
| azure_cloud | missing_credentials: AZURE_SPEECH_KEY,AZURE_SPEECH_REGION |
| google_cloud | missing_credentials: GOOGLE_APPLICATION_CREDENTIALS,GOOGLE_CLOUD_PROJECT |
| aws_cloud | missing_credentials: AWS_TRANSCRIBE_BUCKET |

## Dataset Description

Selected schema-first runs: 4
Dataset used: librispeech_test_clean_subset
Clean source utterances in quality table: 10
Utterance-variant rows in performance and robustness tables: 150
Dataset validation status: passed
Dataset validation report: `reports/datasets/dataset_asset_validation.md`
Credential availability report: `reports/thesis_test/credential_availability.md`

## Hardware And Software Environment

OS: Linux-6.17.0-22-generic-x86_64-with-glibc2.39
Python: 3.12.3
Git branch: main
Git commit: e4a8eedfb3e1449ca83d33cbb1ce95e27ceadba4

## Methodology

Canonical benchmark artifacts are collected into schema-first run directories under `results/runs/<run_id>/`, then exported into thesis tables under `results/thesis_final/`.
Mock and fake providers are excluded from final thesis tables.
Quality results are computed from clean source utterances. Noise robustness is reported separately from clean/noisy utterance variants.

## Canonical Benchmark Artifacts

- `artifacts/benchmark_runs/thesis_local_20260503T184131Z`

## Run Completion

| Run | Total Rows | Successful | Failed |
|---|---:|---:|---:|
| thesis_local_20260503T184131Z | 150 | 149 | 1 |

## Metric Definitions

WER/CER/SER measure recognition quality. Final latency and end-to-end RTF measure ROS2/operator-facing performance. `provider_compute_rtf` is secondary and `real_time_factor` is a deprecated compatibility alias.
Primary RTF = `end_to_end_rtf`. `provider_compute_rtf` is secondary. `real_time_factor` is a deprecated alias retained for compatibility.

## Tables Summary

- `provider_comparison.csv`: 7 rows
- `provider_smoke_tests.csv`: 7 rows
- `quality_table.csv`: 3 rows
- `performance_table.csv`: 3 rows
- `resource_table.csv`: 3 rows
- `noise_robustness_table.csv`: 3 rows
- `cost_deployment_table.csv`: 3 rows
- `scenario_scores.csv`: 3 rows

## Main Findings

The generated CSV tables contain the provider-level quality, performance, resource, robustness, cost and scenario suitability values used for thesis interpretation.

## Limitations

The results are indicative and suitable for bachelor-thesis prototype evaluation, but not a large-scale ASR benchmark.
Cloud providers were configured but not benchmarked because credentials were missing or validation failed.
The canonical benchmark contains 1 failed utterance-variant row(s); failures remain represented in aggregate quality/error metrics.

## Recommendation For ROS2/COCOHRIP

Use local providers for offline ROS2 experiments and cloud providers only when internet access, credentials, latency and cost are acceptable for the laboratory scenario.
