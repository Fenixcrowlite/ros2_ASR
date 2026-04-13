# asr_interfaces

ROS2 message, service, and action definitions shared by the runtime pipeline,
benchmark nodes, legacy nodes, and the gateway ROS client.

## Purpose

This package is the wire contract of the ROS side of the system. It contains
no Python runtime logic; it only defines the message schema used to move audio,
status, recognition results, benchmark requests, and artifact references across
the ROS graph.

## Interface Families

### Messages

- Audio transport:
  `AudioChunk`, `AudioSegment`, `SpeechActivity`
- Recognition results:
  `AsrResult`, `AsrResultPartial`, `WordTimestamp`
- Runtime and node state:
  `NodeStatus`, `SessionStatus`, `AsrEvent`
- Metrics and artifacts:
  `AsrMetrics`, `MetricArtifactRef`, `ResultArtifactRef`
- Benchmark and dataset state:
  `BenchmarkJobStatus`, `DatasetStatus`, `ExperimentSummary`

### Services

- Runtime control:
  `RecognizeOnce`, `GetAsrStatus`, `SetAsrBackend`, `StartRuntimeSession`,
  `StopRuntimeSession`, `ReconfigureRuntime`
- Configuration and catalog:
  `ListBackends`, `ListProfiles`, `ValidateConfig`
- Dataset and benchmark state:
  `RegisterDataset`, `ListDatasets`, `GetBenchmarkStatus`

### Actions

- Runtime and streaming:
  `Transcribe`, `StreamSession`
- Benchmark and datasets:
  `RunBenchmarkExperiment`, `ImportDataset`
- Reporting and model management:
  `GenerateReport`, `DownloadModel`

## Who Uses This Package

- `asr_runtime_nodes` publishes/consumes the modern runtime topics and services.
- `asr_benchmark_nodes` exposes benchmark and dataset actions/services.
- `asr_ros` consumes the legacy service/action contracts.
- `asr_gateway` talks to ROS through these generated interfaces.

## Build Notes

- Build this package before packages that import generated interfaces.
- The package is based on `rosidl_default_generators`.
- Message/API changes here are cross-cutting and usually require downstream
  updates in nodes, gateway serializers, and tests.

## Design Rule

Keep interface messages transport-focused. Business rules, validation, and file
layout knowledge should live in Python packages such as `asr_runtime_nodes`,
`asr_benchmark_core`, or `asr_gateway`, not inside the ROS schema itself.
