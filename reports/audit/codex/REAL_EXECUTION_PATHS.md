# Real Execution Paths

## Runtime

- `web_ui/frontend` -> `/api/runtime/*` -> `GatewayRosClient` -> `asr_runtime_nodes.asr_orchestrator_node`
- `ros2 launch asr_launch runtime_minimal.launch.py` -> runtime node graph -> provider adapters
- `RecognizeOnce` service path -> provider adapter -> `NormalizedAsrResult`

## Benchmarking

- `web_ui/frontend` benchmark page -> `/api/benchmark/run` -> `BenchmarkOrchestrator`
- `make bench` -> `scripts/run_benchmark_core.py` -> `BenchmarkOrchestrator`
- `scripts/run_external_dataset_suite.py` -> `BenchmarkOrchestrator` for direct runs + gateway benchmark API for comparative runs

## Results and reporting

- canonical source of truth: `artifacts/benchmark_runs/<run_id>/...`
- local operator compatibility surface: `results/latest_benchmark_summary.json`, `results/benchmark_results.*`, `results/plots/*`
- `make report` -> `scripts/generate_report.py --input results/latest_benchmark_summary.json`

## Diagnostics and logs

- UI logs page -> `/api/logs`
- gateway -> `asr_gateway.log_views.collect_logs`
- source files: repo log folders + explicit ROS log fallback

## Profile/config resolution

- runtime/provider/benchmark/dataset/metric profiles resolve through `asr_config.resolve_profile`
- provider settings merge through `asr_provider_base.catalog.resolve_provider_execution`
- secret refs resolve through `asr_config.load_secret_ref` + `resolve_secret_ref`
