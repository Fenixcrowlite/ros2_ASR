# asr_benchmark_nodes

ROS2 action/service façade for benchmark execution and dataset management.

## Purpose

This package is the ROS-facing shell around `asr_benchmark_core`. It exposes
long-running benchmark and dataset workflows through actions/services, while the
actual orchestration and file persistence stay in the core library packages.

## Main Node

- `asr_benchmark_nodes/benchmark_manager_node.py`:
  `BenchmarkManagerNode`

Console entry point:

- `benchmark_manager_node = asr_benchmark_nodes.benchmark_manager_node:main`

## Exposed ROS API

- Action: `RunBenchmarkExperiment`
- Action: `ImportDataset`
- Service: `GetBenchmarkStatus`
- Service: `RegisterDataset`
- Service: `ListDatasets`

## Responsibilities

- Accept benchmark action goals and forward them to `BenchmarkOrchestrator`.
- Maintain lightweight in-memory status for active/completed runs.
- Expose dataset import and dataset registry actions/services.
- Translate Python exceptions and result models into ROS messages.

## Dependencies

- `asr_benchmark_core` for actual benchmark execution
- `asr_datasets` for manifest import and registry operations
- `asr_interfaces` for ROS actions/services/messages
- `asr_storage` indirectly through the benchmark orchestrator

## Boundary Rules

- No benchmark logic should be duplicated here.
- No GUI/browser projections should live here.
