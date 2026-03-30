# Target Architecture Proposal

## Layers

### 1. Core domain

- `asr_core`
- `asr_config`
- `asr_datasets`
- `asr_metrics`
- `asr_storage`
- `asr_reporting`

### 2. Provider abstraction

- `asr_provider_base`
- `asr_provider_*`

### 3. Execution engines

- runtime: `asr_runtime_nodes`
- benchmark: `asr_benchmark_core` + `asr_benchmark_nodes`

### 4. Operator/control surfaces

- `asr_gateway`
- `web_ui/frontend`
- `scripts/run_benchmark_core.py`

### 5. Compatibility/legacy ring

- `asr_benchmark`
- `asr_ros`
- `asr_backend_*`
- legacy flat configs and older scripts

## Canonical flows

- Runtime flow: ROS2 nodes + provider profiles + normalized results
- Benchmark flow: benchmark profiles + orchestrator + canonical artifacts
- Reporting flow: canonical summary -> exports/UI
- Logs flow: gateway diagnostics/log scan -> structured UI rendering
