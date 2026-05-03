# Final Thesis ASR Benchmark Report

## Goal And Thesis Alignment

This report summarizes a bachelor thesis prototype for ROS2 ASR integration and experimental comparison of selected commercial and non-commercial ASR systems.

## Tested Providers

Actually tested providers: huggingface_local, vosk_local, whisper_local
Skipped or not present in selected run artifacts: huggingface_api, azure_cloud, google_cloud, aws_cloud

## Dataset Description

Selected schema-first runs: 4
Minimum per-row sample count: 10
Sample counts in these tables are utterance-variant rows and include clean/noisy SNR variants.

## Hardware And Software Environment

OS: Linux-6.17.0-22-generic-x86_64-with-glibc2.39
Python: 3.12.3
Git branch: main
Git commit: 73403779554fdf1966f7b2feeaf024b81f535468

## Methodology

Canonical benchmark artifacts are collected into schema-first run directories under `results/runs/<run_id>/`, then exported into thesis tables under `results/thesis_final/`.
Mock and fake providers are excluded from final thesis tables.

## Metric Definitions

WER/CER/SER measure recognition quality. Final latency and end-to-end RTF measure ROS2/operator-facing performance. `provider_compute_rtf` is secondary and `real_time_factor` is a deprecated compatibility alias.
RTF in this thesis means end-to-end real-time factor unless explicitly stated otherwise.

## Tables Summary

- `provider_comparison.csv`: 7 rows
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
Confidence calibration is diagnostic only unless at least 30 confidence-bearing utterances are available.
Cloud provider results are absent from the selected run artifacts; cloud comparison remains pending until credentials and runs are available.

## Recommendation For ROS2/COCOHRIP

Use local providers for offline ROS2 experiments and cloud providers only when internet access, credentials, latency and cost are acceptable for the laboratory scenario.

## Artifacts

