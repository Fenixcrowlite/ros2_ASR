# System Overview

## Purpose
Modular ROS2-first ASR platform for:
- runtime speech recognition in robotics scenarios,
- reproducible benchmark/evaluation experiments,
- profile-driven deployment and iteration,
- GUI-driven operation via gateway (without GUI owning core logic).

## Subsystems
1. Runtime ASR subsystem
- ROS2 nodes: audio input, preprocessing, VAD segmentation, ASR orchestration.
- Provider adapters with normalized output contract.
- Session/status topics and runtime control services.

2. Benchmark/Evaluation subsystem
- Dataset registry/import/manifest.
- Benchmark orchestrator + batch executor.
- Metric plugins (WER/CER/latency/success/failure baseline).
- Reproducible run artifacts with immutable manifests and config snapshots.

3. Gateway/UI subsystem
- `asr_gateway` backend API as control boundary.
- `web_ui` frontend skeleton consuming gateway endpoints.
- No direct GUI coupling with internal runtime components.

## Target package map
- Contracts: `asr_interfaces`
- Shared core: `asr_core`
- Config: `asr_config`
- Provider contract + adapters: `asr_provider_base`, `asr_provider_*`
- Runtime nodes: `asr_runtime_nodes`
- Datasets: `asr_datasets`
- Metrics/reporting: `asr_metrics`, `asr_reporting`
- Benchmark: `asr_benchmark_core`, `asr_benchmark_nodes`
- Storage/artifacts: `asr_storage`
- Gateway: `asr_gateway`
- Launch: `asr_launch`

## Namespace strategy
- `/asr/runtime/...`
- `/asr/providers/...`
- `/asr/status/...`
- `/benchmark/...`
- `/datasets/...`
- `/config/...`
- `/gateway/...`

Future multi-instance pattern:
- `/robot_1/asr/...`
- `/robot_2/asr/...`
