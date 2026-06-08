# asr_benchmark_core

Canonical benchmark orchestration and execution core for the modern ASR stack.

## Purpose

This package turns a high-level benchmark request into a reproducible run:

1. resolve profiles and scenarios
2. expand the provider x sample x variant matrix
3. execute providers on every sample
4. compute metrics
5. persist artifacts and summaries

It is the benchmark control plane. ROS exposure lives in `asr_benchmark_nodes`,
and browser/API exposure lives in `asr_gateway`.

## Main Responsibilities

- Resolve benchmark, dataset, metric, and provider profiles.
- Build a fully expanded benchmark execution plan.
- Execute both batch and streaming benchmark paths.
- Compute per-sample metrics through `asr_metrics`.
- Persist manifests, raw outputs, normalized outputs, reports, and traces.
- Generate deterministic synthetic noise variants for robustness experiments.

## Key Modules

- `asr_benchmark_core/orchestrator.py`: `BenchmarkOrchestrator`,
  `ResolvedBenchmarkPlan`, and the top-level run flow.
- `asr_benchmark_core/executor.py`: `BatchExecutor` for one concrete
  sample/provider execution path.
- `asr_benchmark_core/noise.py`: deterministic noise catalogs, scenario
  normalization, and WAV corruption helpers.
- `asr_benchmark_core/models.py`: request/result/summary dataclasses.
- `asr_benchmark_core/scenarios.py`: named benchmark scenario registry.

## Noise Robustness Model

- `clean_baseline` remains the control condition.
- Severity tiers map to SNR values:
  `light=30 dB`, `medium=20 dB`, `heavy=10 dB`, `extreme=0 dB`.
- Noise family is independent from severity.
- Current synthetic noise families:
  `white`, `pink`, `brown`, `babble`, `hum`.
- A fixed seed keeps augmentation reproducible across runs.

## Inputs

- Config profiles from `asr_config`
- Dataset manifests from `asr_datasets`
- Provider adapters from `asr_provider_base`
- Metric definitions and engines from `asr_metrics`
- Artifact layout from `asr_storage`

## Outputs

- Run manifest and resolved config snapshots
- Raw provider outputs
- Normalized outputs
- Metric rows and summaries
- Markdown/JSON/CSV reports
- Optional observability traces

## Boundary Rules

- No ROS actions/services in this package.
- No FastAPI endpoints in this package.
- No browser-specific read models in this package.

## Read This Package In This Order

1. `asr_benchmark_core/orchestrator.py`
2. `asr_benchmark_core/executor.py`
3. `asr_benchmark_core/noise.py`
4. `asr_benchmark_core/scenarios.py`
5. `asr_benchmark_core/models.py`
