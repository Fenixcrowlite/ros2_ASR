# Real Execution Paths

| Path ID | Entry Point | Core Modules | Outputs | Status |
|---|---|---|---|---|
| runtime_segmented | `ros2 launch asr_launch runtime_minimal.launch.py` or gateway runtime start | `asr_runtime_nodes` + `asr_provider_base` + `asr_provider_*` | runtime topics, status topics, gateway live state | canonical |
| runtime_gateway | `ros2 launch asr_launch gateway_with_runtime.launch.py` | runtime stack + `asr_gateway` | HTTP API + browser UI + runtime topics | canonical |
| runtime_full_stack | `ros2 launch asr_launch full_stack_dev.launch.py` | runtime stack + gateway + benchmark manager | full operator surface | canonical |
| runtime_provider_stream | runtime start with `processing_mode=provider_stream` | orchestrator + streaming-capable provider adapters | partial/final runtime results | canonical |
| recognize_once_direct | `POST /api/runtime/recognize_once` | gateway -> ROS client -> orchestrator -> provider manager | normalized direct result payload | canonical |
| benchmark_core_direct | Python call into `BenchmarkOrchestrator.run(...)` | `asr_benchmark_core` + `asr_metrics` + `asr_storage` | run manifest, metrics, reports, artifacts | canonical |
| benchmark_operator_cli | `scripts/run_benchmark_core.py` / `scripts/run_benchmarks.sh` | benchmark core + compatibility export bridge | canonical run folder + `results/latest_benchmark_summary.json` + compatibility `results/*.json/csv/png` | canonical |
| benchmark_ros | `/benchmark/run_experiment` action | `asr_benchmark_nodes` -> `asr_benchmark_core` | benchmark action feedback + artifacts | canonical |
| provider_validation | `POST /api/providers/validate` and provider catalog pages | gateway + `ProviderManager` | provider validity/status/capability previews | canonical |
| legacy_runtime | `ros2 launch asr_ros bringup.launch.py` | `asr_ros` + `asr_core.factory` + `asr_backend_*` | old `/asr/*` services/topics | compatibility |
| legacy_flat_benchmark | `python -m asr_benchmark.runner` | `asr_benchmark` + `MetricsCollector` + legacy report flow | flat `results/*.json/csv/png` | compatibility / non-canonical |

## Canonical Path Decision

Use these paths as the engineering baseline:

- Runtime: `asr_launch` + `asr_runtime_nodes` + provider adapters
- Benchmark: `asr_benchmark_core` + `asr_benchmark_nodes`
- UI/API: `asr_gateway` + `web_ui`
- Artifacts: `asr_storage` under `artifacts/benchmark_runs/`

Treat these as compatibility only:

- `asr_ros`
- `asr_benchmark`
- `configs/default.yaml`
- direct `python -m asr_benchmark.runner` usage

Treat these as compatibility mirrors generated from the canonical benchmark run:

- `results/benchmark_results.*`
- `results/plots/*`
- `results/latest_benchmark_summary.json`
- `results/latest_benchmark_run.json`
