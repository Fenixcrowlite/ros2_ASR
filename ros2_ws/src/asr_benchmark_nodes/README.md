# asr_benchmark_nodes

ROS2 action/service layer for benchmark subsystem.

## Exposed API
- Action: `RunBenchmarkExperiment`
- Action: `ImportDataset`
- Service: `GetBenchmarkStatus`
- Service: `RegisterDataset`
- Service: `ListDatasets`

## Boundaries
- Delegates execution to `asr_benchmark_core`.
