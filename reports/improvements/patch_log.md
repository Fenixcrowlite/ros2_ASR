# Patch Log

Generated at: `2026-03-31T12:24:00+00:00`

This log records the changes made in this remediation pass only.

## 1. Canonical workflow and legacy isolation hardening

Changed files:

- [Makefile](/home/fenix/Desktop/ros2ws/Makefile)
- [scripts/source_runtime_env.sh](/home/fenix/Desktop/ros2ws/scripts/source_runtime_env.sh)
- [tests/integration/test_source_runtime_env.py](/home/fenix/Desktop/ros2ws/tests/integration/test_source_runtime_env.py)
- [tests/integration/test_cli_flows.py](/home/fenix/Desktop/ros2ws/tests/integration/test_cli_flows.py)
- [README.md](/home/fenix/Desktop/ros2ws/README.md)

Reason:

- canonical build/test defaults were already isolated at `colcon` level, but Python import path still allowed silent legacy bleed-through

Validation:

- `pytest -q tests/integration/test_source_runtime_env.py`
- `make test-unit`

## 2. Runtime correctness fixes

Changed files:

- [audio_preprocess_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py)
- [vad_segmenter_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py)
- [runtime.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_observability/validators/runtime.py)
- [dataset.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark/asr_benchmark/dataset.py)
- [tests/unit/test_runtime_audio_pipeline.py](/home/fenix/Desktop/ros2ws/tests/unit/test_runtime_audio_pipeline.py)
- [tests/unit/test_runtime_trace_validator.py](/home/fenix/Desktop/ros2ws/tests/unit/test_runtime_trace_validator.py)
- [tests/unit/test_dataset.py](/home/fenix/Desktop/ros2ws/tests/unit/test_dataset.py)

Reason:

- close confirmed defects in payload handling, metric validation, and deterministic manifest resolution

Validation:

- `pytest -q tests/unit/test_runtime_trace_validator.py`
- `pytest -q tests/unit/test_dataset.py tests/unit/test_runtime_audio_pipeline.py`

## 3. Gateway lifecycle and readiness semantics

Changed files:

- [ros_client.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_gateway/asr_gateway/ros_client.py)
- [api.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_gateway/asr_gateway/api.py)
- [tests/unit/test_gateway_ros_client.py](/home/fenix/Desktop/ros2ws/tests/unit/test_gateway_ros_client.py)
- [tests/api/test_gateway_api.py](/home/fenix/Desktop/ros2ws/tests/api/test_gateway_api.py)

Reason:

- remove request-scoped ROS client churn and stop overstating provider readiness in the gateway/API layer

Validation:

- `pytest -q tests/unit/test_gateway_ros_client.py`
- `pytest -q tests/api/test_gateway_api.py::test_provider_catalog_distinguishes_ready_and_degraded_profiles`

## 4. Runtime observability and transport telemetry

Changed files:

- [transport.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/transport.py)
- [audio_input_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py)
- [audio_preprocess_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py)
- [vad_segmenter_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py)
- [asr_orchestrator_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py)
- [tests/unit/test_runtime_observability_export.py](/home/fenix/Desktop/ros2ws/tests/unit/test_runtime_observability_export.py)

Reason:

- live runtime lacked persisted traces and transport-level latency/drop observability

Validation:

- `pytest -q tests/unit/test_runtime_observability_export.py`
- `make test-ros`

## 5. Model-load metrics, CI, and dependency organization

Changed files:

- [manager.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_provider_base/asr_provider_base/manager.py)
- [__init__.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_provider_base/asr_provider_base/__init__.py)
- [runtime.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_observability/analyzers/runtime.py)
- [files.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_observability/exporters/files.py)
- [executor.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py)
- [orchestrator.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py)
- [noise.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py)
- [requirements.txt](/home/fenix/Desktop/ros2ws/requirements.txt)
- [requirements/](/home/fenix/Desktop/ros2ws/requirements)
- [.github/workflows/ci.yml](/home/fenix/Desktop/ros2ws/.github/workflows/ci.yml)

Reason:

- model load / warm-cold metrics were missing, dependency installation was monolithic, and CI lacked security + failure artifact handling

Validation:

- `pytest -q tests/component/test_provider_manager.py`
- `make security-scan`
- `bash scripts/secret_scan.sh`
- `make lint-ruff`
- `make lint-mypy`
- `python scripts/run_benchmark_core.py --benchmark-profile default_benchmark --run-id audit_20260331_risk_closure_final`

## 6. Benchmark aggregate quarantine and action latency telemetry

Changed files:

- [summary.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/summary.py)
- [orchestrator.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py)
- [ros_client.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_gateway/asr_gateway/ros_client.py)
- [test_metric_summary.py](/home/fenix/Desktop/ros2ws/tests/unit/test_metric_summary.py)
- [test_gateway_ros_client.py](/home/fenix/Desktop/ros2ws/tests/unit/test_gateway_ros_client.py)
- [test_benchmark_orchestrator.py](/home/fenix/Desktop/ros2ws/tests/component/test_benchmark_orchestrator.py)

Reason:

- close the remaining observability/reporting gaps by making corrupted benchmark rows non-poisoning for aggregate summaries and by exporting generic ROS action latency metrics from the gateway helper

Validation:

- `pytest -q tests/unit/test_metric_summary.py`
- `pytest -q tests/unit/test_gateway_ros_client.py`
- `pytest -q tests/component/test_benchmark_orchestrator.py`
- `pytest -q tests/integration/test_cli_flows.py::test_run_benchmark_core_cli_exports_canonical_and_compatibility_artifacts`
- `make lint-ruff`
- `make lint-mypy`
