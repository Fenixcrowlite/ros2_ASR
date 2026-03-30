# Target Architecture Proposal

## Layered Structure

### Platform core

- `asr_config`
- `asr_core`
- `asr_provider_base`
- `asr_provider_*`
- `asr_datasets`
- `asr_metrics`
- `asr_storage`
- `asr_benchmark_core`

### ROS2 transport / orchestration

- `asr_runtime_nodes`
- `asr_benchmark_nodes`
- `asr_launch`
- `asr_interfaces`

### Control plane

- `asr_gateway`
- `web_ui`
- `scripts/run_benchmark_core.py`
- `scripts/generate_report.py`

### Compatibility boundary

- `asr_ros`
- `asr_benchmark`
- `asr_backend_*`
- `configs/default.yaml`
- legacy scripts/report flow

## Canonical Runtime Flow

`runtime_profile + provider_profile -> runtime nodes -> provider adapter -> normalized result -> gateway/UI`

## Canonical Benchmark Flow

`benchmark_profile + dataset_profile + metric_profiles + provider_profiles -> benchmark core -> artifact store -> summary pointer + compatibility export`

## Storage Contract

All reproducible benchmark artifacts should converge on:

- `artifacts/benchmark_runs/<run_id>/manifest/`
- `artifacts/benchmark_runs/<run_id>/metrics/`
- `artifacts/benchmark_runs/<run_id>/reports/`
- optional `raw_outputs/` and `normalized_outputs/`

## Migration Direction

1. Keep compatibility modules running only as wrappers or migration aids.
2. Keep `results/benchmark_results.*` only as compatibility mirrors; make `results/latest_benchmark_summary.json` and `artifacts/benchmark_runs/<run_id>/reports/summary.json` the primary operator-facing summary surfaces.
3. Make gateway/UI read and write only the canonical runtime/benchmark contracts.
