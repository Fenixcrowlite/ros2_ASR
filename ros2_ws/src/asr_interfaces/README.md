# asr_interfaces

ROS2 messages, services, and actions shared by the canonical runtime, benchmark, and gateway layers.

## Purpose

This package defines transport contracts only. It contains no runtime business logic.

## Main Consumers

- `asr_runtime_nodes`
- `asr_benchmark_nodes`
- `asr_gateway`

## Notes

- `RecognizeOnce` remains the canonical one-shot ROS service.
- `ListBackends` remains a compatibility-named provider catalog contract.
- `SetAsrBackend` stays in the IDL only for compatibility and is not part of the primary production runbook.
