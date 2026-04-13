# Codebase Reading Guide

This document is the shortest practical route through the repository for an engineer who wants to understand how the system actually works without reading 30k lines in random order.

## 1. Start Here

Read these first:

- `README.md`
- `docs/architecture/system_overview.md`
- `docs/architecture/runtime_architecture.md`
- `docs/architecture/benchmark_architecture.md`

These explain the intended boundaries. The code then becomes much easier to interpret because you know which package owns runtime, benchmarking, metrics, or gateway behavior.

## 2. High-Level Mental Model

The repository is split into four operational layers:

1. Shared primitives
   - `asr_core`
   - provider-neutral models, IDs, audio helpers, namespace constants
2. Runtime execution
   - `asr_runtime_nodes`
   - `asr_provider_base`
   - `asr_provider_*`
   - live ROS pipeline and provider invocation
3. Benchmark execution
   - `asr_datasets`
   - `asr_benchmark_core`
   - `asr_benchmark_nodes`
   - `asr_metrics`
   - offline reproducible experiment runs
4. Gateway and browser UI
   - `asr_gateway`
   - `web_ui`
   - HTTP control plane over the ROS/runtime/benchmark stack

## 3. Read Runtime Path in This Order

When the goal is to understand live ASR execution:

1. `ros2_ws/src/asr_runtime_nodes/README.md`
2. `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py`
3. `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py`
4. `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py`
5. `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py`
6. `ros2_ws/src/asr_provider_base/asr_provider_base/manager.py`
7. one concrete provider package such as:
   - `ros2_ws/src/asr_provider_whisper/asr_provider_whisper/whisper_provider.py`
   - `ros2_ws/src/asr_provider_azure/asr_provider_azure/azure_provider.py`
   - `ros2_ws/src/asr_provider_aws/asr_provider_aws/aws_provider.py`

What to keep in mind:

- `audio_input_node` owns acquisition and replay pacing.
- `audio_preprocess_node` normalizes format before downstream use.
- `vad_segmenter_node` converts a chunk stream into speech segments in `segmented` mode.
- `asr_orchestrator_node` is the runtime control plane and the only node that talks to providers.
- provider packages should be read as adapters, not as owners of the runtime graph.

## 4. Read Gateway/UI Path in This Order

When the goal is to understand the browser-driven control plane:

1. `ros2_ws/src/asr_gateway/README.md`
2. `ros2_ws/src/asr_gateway/asr_gateway/api.py`
3. `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py`
4. `ros2_ws/src/asr_gateway/asr_gateway/result_views.py`
5. `ros2_ws/src/asr_gateway/asr_gateway/log_views.py`
6. `web_ui/README.md`
7. `web_ui/frontend/js/app.js`
8. `web_ui/frontend/js/api.js`
9. one task page at a time:
   - `web_ui/frontend/js/pages/runtime.js`
   - `web_ui/frontend/js/pages/benchmark.js`
   - `web_ui/frontend/js/pages/results.js`
   - `web_ui/frontend/js/pages/secrets.js`

What to keep in mind:

- `api.py` is the HTTP façade and normalization layer.
- `ros_client.py` hides ROS services/actions/topics behind a gateway-friendly shape.
- `result_views.py` and `log_views.py` are projection helpers for GUI-facing read models.
- the browser never talks to ROS directly; it always goes through gateway endpoints.

## 5. Read Benchmark Path in This Order

When the goal is to understand offline experiments and reports:

1. `ros2_ws/src/asr_benchmark_core/README.md`
2. `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py`
3. `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py`
4. `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py`
5. `ros2_ws/src/asr_metrics/README.md`
6. `ros2_ws/src/asr_metrics/asr_metrics/engine.py`
7. `ros2_ws/src/asr_metrics/asr_metrics/summary.py`
8. `ros2_ws/src/asr_reporting/asr_reporting/exporter.py`

What to keep in mind:

- the orchestrator resolves profiles and builds the run plan.
- the executor runs one provider against one sample/variant at a time.
- metrics are evaluated after provider output is normalized.
- reports and exported comparisons are projections of stored run artifacts, not the primary source of truth.

## 6. Configuration and Profiles

These directories matter before changing behavior:

- `configs/runtime`
- `configs/providers`
- `configs/benchmark`
- `configs/datasets`
- `configs/metrics`

And these modules explain how profiles are resolved:

- `ros2_ws/src/asr_config/asr_config/loader.py`
- `ros2_ws/src/asr_config/asr_config/validation.py`
- `ros2_ws/src/asr_provider_base/asr_provider_base/catalog.py`

Important rule:

- runtime behavior is often a combination of profile defaults plus request-time overrides; do not reason from YAML or request payload alone.

## 7. Artifacts and Persistence

Persistent outputs are distributed intentionally:

- `artifacts/benchmark_runs/...` is the canonical benchmark artifact tree
- `artifacts/runtime_sessions/...` is the runtime/session artifact tree
- `results/...` contains compatibility exports and human-facing summaries
- `datasets/...` contains manifests, imported files, registry metadata, and derived dataset material

Read these modules when debugging stored state:

- `ros2_ws/src/asr_storage/asr_storage/artifacts.py`
- `ros2_ws/src/asr_gateway/asr_gateway/result_views.py`
- `ros2_ws/src/asr_gateway/asr_gateway/runtime_assets.py`

## 8. Where New Engineers Usually Get Lost

Common traps:

- confusing legacy packages (`asr_ros`, `asr_benchmark`) with the canonical path
- reading provider packages before understanding `asr_orchestrator_node`
- inspecting GUI JS before understanding gateway endpoint semantics
- assuming `results/` is the source of truth instead of `artifacts/`
- assuming one metric field means the same thing across legacy and canonical artifacts without checking metrics semantics version

## 9. Recommended Change Strategy

For safe changes:

1. Identify which layer owns the behavior.
2. Find the profile or request normalization point.
3. Trace the canonical path through gateway/runtime/benchmark.
4. Change the smallest owning module.
5. Update the projection layer only if the stored contract changed.

This reading order is intentionally biased toward ownership and data flow, because that is what keeps the repository understandable when it grows.
