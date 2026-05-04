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

The active dataset contains 10 clean LibriSpeech utterances. For robustness evaluation, each utterance is also evaluated under derived white-noise SNR variants. Therefore quality tables use 10 clean source utterances per provider preset, while performance and robustness tables aggregate 50 utterance-variant rows per provider preset: 10 clean utterances x 5 acoustic conditions. The final primary evidence contains 550 utterance-variant rows across 11 valid provider presets.

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

## Evidence Structure

Primary evidence:

- tiered benchmark runs: fast_or_low_resource, balanced and accurate_or_high_quality

Supporting evidence:

- local matrix run
- cloud matrix run
- provider smoke tests
- credential availability report
- dataset validation report
- thesis evidence validation report

## Hardware And Software Environment

OS: Linux-6.17.0-22-generic-x86_64-with-glibc2.39
Python: 3.12.3
Git branch: main
Git commit: 5bbecddf1672cb7a9dc28ba5233daa01e106dbe0

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

## Metric Family Rationale

The thesis uses multiple metric families because ASR provider suitability in robotics is multi-objective. A single global score is not used as the primary result because provider suitability depends on the deployment scenario.

Recognition quality, performance, real-time behavior, robustness, resource usage, cost, deployment constraints and scenario suitability are interpreted separately. This prevents a low-WER cloud provider from being treated as automatically best when it may require internet access, credentials, higher latency or non-local execution. The metric families are documented in `docs/metric_families.md`.

## Scenario Score Methodology

Scenario scores are normalized heuristic suitability scores derived from quality, latency, RTF, robustness, deployment constraints and cost-related fields. They are not independent benchmark measurements.

The score should not be interpreted as an absolute scientific metric. It is a decision-support index for this bachelor thesis prototype.

## Tables Summary

- `provider_comparison.csv`: 7 rows; implemented provider capabilities, deployment type and credential requirements.
- `provider_smoke_tests.csv`: 7 rows; provider availability, credential detection and one-sample recognition smoke test.
- `quality_table.csv`: 11 rows; clean-source WER/CER/SER comparison; confidence intervals are marked not_computed because the sample set is thesis-scale.
- `performance_table.csv`: 11 rows; latency, RTF, throughput and real-time admissibility.
- `resource_table.csv`: 11 rows; CPU/RAM/GPU/model-size observations with availability flags.
- `noise_robustness_table.csv`: 11 rows; WER degradation under SNR 20, 10, 5 and 0 dB.
- `cost_deployment_table.csv`: 11 rows; local/cloud deployment constraints, direct API cost semantics and cost availability flags.
- `scenario_scores.csv`: 11 rows; normalized heuristic suitability scores for embedded, batch, analytics and dialog scenarios.

## Plot Interpretation Guide

- `wer_by_provider.png` - Clean WER by Provider Preset. Lower is better. Computed on 10 clean LibriSpeech source utterances.
- `cer_by_provider.png` - Clean CER by Provider Preset. CER complements WER by showing character-level transcription errors. Lower is better.
- `latency_p95_by_provider.png` - P95 Final Latency by Provider Preset. Lower p95 latency indicates more predictable response time for interactive ROS2 use.
- `rtf_by_provider.png` - End-to-End RTF by Provider Preset. RTF < 1 indicates faster-than-real-time processing. The RTF = 1 threshold separates faster and slower than real time.
- `wer_vs_latency_pareto.png` - WER vs P95 Latency Trade-off. Lower-left points represent better quality-latency trade-off. Local and cloud providers are marked separately where plot data is available.
- `noise_robustness_by_provider.png` - WER Degradation Under Synthetic Noise. Synthetic white noise was used, so results show robustness trends, not full real-world acoustic coverage.
- `scenario_scores.png` - Scenario Suitability Scores. Higher scores indicate stronger heuristic suitability for the scenario; scores are normalized decision-support indices, not direct benchmark measurements.
- `cost_vs_quality.png` - Cost vs Recognition Quality. Lower WER and lower direct API cost are preferable. Local providers have zero direct API cost; hardware and maintenance costs are not monetized.

## Main Findings

The benchmark confirmed that all selected local providers and three commercial cloud providers can be integrated into the ROS2 ASR evaluation workflow.

In the fast_or_low_resource tier, local providers were more suitable for offline ROS2 usage. Hugging Face local light and Whisper local light had low end-to-end RTF values and did not require internet access or credentials. Vosk remained useful as a low-resource offline baseline, but showed the highest WER and the strongest degradation under heavy noise.

In the balanced tier, Azure Speech and AWS Transcribe achieved the lowest clean WER in this small LibriSpeech subset, while Hugging Face local balanced provided the strongest local/offline quality-performance compromise. AWS produced strong recognition quality but was not admissible for embedded-style real-time use because its mean end-to-end RTF exceeded 1.0.

In the accurate_or_high_quality tier, Whisper local accurate achieved lower clean WER than Google Cloud accurate in this experiment, while Google Cloud accurate had competitive latency. Hugging Face local accurate could not be evaluated because the workstation ran out of GPU memory, so that high-memory preset remains a failed preset attempt rather than a metric-table row.

Noise robustness results showed that provider behavior differs strongly under SNR degradation. Vosk local degraded the most at SNR 0 in the fast tier, while AWS standard showed the smallest WER degradation in the balanced tier. These results are indicative only because the benchmark uses 10 clean source utterances and derived noisy variants.

## Limitations

The results are indicative and suitable for bachelor-thesis prototype evaluation, but not a large-scale ASR benchmark.
The canonical benchmark contains 52 failed utterance-variant row(s). Completely failed presets are reported as failed attempts and excluded from quality/performance ranking tables.

## Recommendation For ROS2/COCOHRIP

For offline ROS2 laboratory experiments, Whisper local should be used as the primary local baseline because it provides a good balance of quality, reproducibility and independence from cloud services. Hugging Face local is useful when cached models and sufficient hardware are available, but high-memory presets must be treated carefully. Vosk remains useful as a lightweight offline baseline, especially for low-resource experiments, but it should not be selected as the highest-accuracy option based on this benchmark.

For cloud-assisted ASR, Azure Speech, Google Speech-to-Text and AWS Transcribe are suitable only when external connectivity, credentials, latency and cost are acceptable. AWS Transcribe achieved strong recognition quality in the balanced tier, but its measured end-to-end RTF and latency make it less suitable for interactive embedded-style ROS2 control in this prototype.

The recommended thesis conclusion is therefore a hybrid architecture: local ASR providers for reproducible offline robot experiments, and cloud ASR providers for optional high-quality transcription or comparative benchmarking.
