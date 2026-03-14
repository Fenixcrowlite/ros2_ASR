# Benchmark Architecture

## Core components
1. `asr_datasets`
- Manifest model (`jsonl`), validation, folder import, registry.

2. `asr_benchmark_core`
- `BenchmarkOrchestrator`: resolves profiles, creates run, persists manifests.
- `BatchExecutor`: sample x provider matrix execution.
- Scenario manager with baseline scenario set.

3. `asr_metrics`
- Plugin-style metric engine.
- Baseline plugins: `wer`, `cer`, `total_latency_ms`, `success_rate`, `failure_rate`.

4. `asr_benchmark_nodes`
- ROS actions/services for benchmark runs and dataset import/registration.

## Reproducibility guarantees per run
Each run stores:
- immutable run manifest,
- config snapshots,
- provider/dataset refs,
- environment metadata,
- raw outputs,
- normalized outputs,
- metric outputs,
- report outputs.

All benchmark runs are isolated by stable `run_id` in `artifacts/benchmark_runs/<run_id>/...`.
