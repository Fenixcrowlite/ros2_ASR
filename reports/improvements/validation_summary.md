# Validation Summary

Generated at: `2026-03-31T12:24:00+00:00`

## Commands Run

```bash
pytest -q tests/unit/test_runtime_trace_validator.py
pytest -q tests/unit/test_dataset.py tests/unit/test_runtime_audio_pipeline.py
pytest -q tests/unit/test_metric_summary.py
pytest -q tests/integration/test_source_runtime_env.py
pytest -q tests/integration/test_cli_flows.py::test_run_benchmark_core_cli_exports_canonical_and_compatibility_artifacts
pytest -q tests/component/test_provider_manager.py
pytest -q tests/component/test_benchmark_orchestrator.py
pytest -q tests/unit/test_gateway_ros_client.py
pytest -q tests/api/test_gateway_api.py::test_provider_catalog_distinguishes_ready_and_degraded_profiles tests/api/test_gateway_api.py::test_runtime_api_round_trip
pytest -q tests/unit/test_runtime_audio_pipeline.py tests/unit/test_runtime_orchestrator_state.py tests/unit/test_runtime_orchestrator_stream_errors.py tests/unit/test_runtime_orchestrator_recognize_once.py
pytest -q tests/unit/test_audio_input_node.py
pytest -q tests/unit/test_runtime_observability_export.py
make lint-ruff
make lint-mypy
make security-scan
bash scripts/secret_scan.sh
make build
make test-unit
make test-ros
make test-colcon
source .venv/bin/activate && python scripts/run_benchmark_core.py --benchmark-profile default_benchmark --run-id audit_20260331_risk_closure_final
```

## Results

- `pytest -q tests/unit/test_runtime_trace_validator.py`
  - passed
  - validator now accepts valid `wer`/`cer > 1.0`
- `pytest -q tests/unit/test_dataset.py tests/unit/test_runtime_audio_pipeline.py`
  - passed
  - deterministic legacy manifest resolution and hot-path binary payload handling verified
- `pytest -q tests/unit/test_metric_summary.py`
  - passed
  - corrupted benchmark rows are excluded from aggregate metrics while total run counts remain preserved
- `pytest -q tests/integration/test_source_runtime_env.py`
  - passed
  - canonical `PYTHONPATH` excludes legacy packages by default and supports explicit opt-in
- `pytest -q tests/integration/test_cli_flows.py::test_run_benchmark_core_cli_exports_canonical_and_compatibility_artifacts`
  - passed
  - canonical benchmark CLI still exports expected compatibility artifacts
- `pytest -q tests/component/test_provider_manager.py`
  - passed
  - provider load/warm-cold metadata verified
- `pytest -q tests/component/test_benchmark_orchestrator.py`
  - passed
  - benchmark summary/report generation remains valid with corrupted-row aggregate quarantine enabled
- `pytest -q tests/unit/test_gateway_ros_client.py`
  - passed
  - persistent gateway ROS bridge behavior and action latency metrics verified
- `pytest -q tests/api/test_gateway_api.py::test_provider_catalog_distinguishes_ready_and_degraded_profiles tests/api/test_gateway_api.py::test_runtime_api_round_trip`
  - passed
  - provider catalog readiness semantics and runtime API roundtrip verified
- `pytest -q tests/unit/test_runtime_audio_pipeline.py tests/unit/test_runtime_orchestrator_state.py tests/unit/test_runtime_orchestrator_stream_errors.py tests/unit/test_runtime_orchestrator_recognize_once.py`
  - passed
  - runtime transport telemetry and trace-aware orchestrator paths remain stable
- `pytest -q tests/unit/test_audio_input_node.py`
  - passed
  - audio-source transport metadata publication verified
- `pytest -q tests/unit/test_runtime_observability_export.py`
  - passed
  - segmented and provider-stream runtime traces exported to artifacts
- `make lint-ruff`
  - passed
- `make lint-mypy`
  - passed
- `make security-scan`
  - passed
- `bash scripts/secret_scan.sh`
  - passed
- `make build`
  - passed
  - summary: `24 packages finished`
- `make test-unit`
  - passed
- `make test-ros`
  - passed
  - canonical ROS integration selection: `2` tests
- `make test-colcon`
  - passed
  - canonical colcon smoke suite passed across `24` packages
- benchmark run `audit_20260331_risk_closure_final`
  - passed
  - `1/1` samples successful
  - run dir: `artifacts/benchmark_runs/audit_20260331_risk_closure_final`

## Key measurable outcomes

- benchmark `WER = 0.0`
- benchmark `CER = 0.0`
- benchmark `total_latency_ms = 1974.159280071035`
- benchmark `RTF = 0.23762148291659063`
- benchmark `model_load_ms = 3.129232`
- benchmark `provider_init_cold_start = true`
- benchmark `provider_call_cold_start = true`
- runtime segmented/provider-stream flows now produce persisted trace JSON/CSV artifacts under `artifacts/runtime_sessions/<session_id>/metrics/`
- gateway action flows now export `action_goal_wait_ms`, `action_result_wait_ms`, `action_latency_ms`, and `ros_action_latency_ms`
- benchmark summaries now quarantine corrupted rows from aggregate metrics and expose `aggregate_samples` / `corrupted_samples`
