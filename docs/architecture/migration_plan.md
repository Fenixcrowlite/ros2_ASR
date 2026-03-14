# Migration Plan: Legacy Stack -> Modular ROS2-First ASR Platform

## Scope
Migrate from legacy packages (`asr_ros`, `asr_benchmark`, `asr_backend_*`, flat config/web orchestration) to modular baseline with separate runtime, providers, benchmark, storage, and gateway layers.

## Phase 0: Assessment and freeze
- Produce repository assessment (`repo_assessment.md`).
- Identify reusable code paths and legacy modules for deprecation.
- Preserve existing behavior as reference baseline.

## Phase 1: Structural baseline (non-destructive)
- Create target ROS2 package skeletons.
- Create target top-level directory structure (`configs/*`, `secrets/*`, `datasets/*`, `artifacts/*`, `logs/*`, `web_ui/*`, `scripts/*`).
- Add package READMEs and TODO roadmaps.

## Phase 2: Contract baseline
- Expand `asr_interfaces` with runtime/benchmark/gateway contracts.
- Introduce provider adapter contract in `asr_provider_base`.
- Introduce normalized result model in `asr_core` for provider-independent output.

## Phase 3: Runtime vertical slice
- Implement `audio_input_node`, `audio_preprocess_node`, `vad_segmenter_node`, `asr_orchestrator_node` in `asr_runtime_nodes`.
- Integrate provider adapters (`whisper` local, `azure` cloud baseline).
- Publish normalized partial/final results and session/node status.

## Phase 4: Config/secrets/storage baseline
- Implement profile-driven resolver in `asr_config`.
- Implement secret reference model and masked resolution.
- Implement artifact persistence layer in `asr_storage` with run/session manifest snapshots.

## Phase 5: Benchmark baseline
- Implement dataset registry/ingestion/manifest model (`asr_datasets`).
- Implement benchmark orchestration/execution and plugin metrics (`asr_benchmark_core`, `asr_metrics`).
- Expose benchmark services/actions via `asr_benchmark_nodes`.

## Phase 6: Gateway + web baseline
- Implement `asr_gateway` API and ROS interaction façade.
- Provide `web_ui` frontend/backend skeleton pages.
- Keep legacy `web_gui` functional but mark deprecated.

## Phase 7: Launch, docs, and compatibility notes
- Add `asr_launch` scenarios.
- Update architecture docs and implementation report.
- Record deprecated modules and transitional compatibility points.

## Legacy compatibility policy
- Keep legacy packages buildable during migration.
- Prefer additive changes to interfaces where possible.
- Mark legacy launch/web flows as deprecated in docs.

## Deprecation targets
- `asr_ros` -> replaced by `asr_runtime_nodes`.
- `asr_benchmark` -> replaced by `asr_benchmark_core` + `asr_benchmark_nodes`.
- `asr_backend_*` -> replaced by `asr_provider_*` packages.
- Flat `configs/*.yaml` -> replaced by profile directories and resolved snapshots.
- `web_gui` control-plane logic -> replaced by `asr_gateway`.

## Verification checkpoints
1. `colcon build --base-paths ros2_ws/src --symlink-install`
2. Runtime minimal launch publishes normalized final result.
3. Benchmark single-provider run generates immutable run folder with manifest + metrics.
4. Gateway can trigger runtime and benchmark APIs.

