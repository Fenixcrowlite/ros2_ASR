# Interfaces

## Canonical Runtime Surface

Primary runtime control lives in `asr_runtime_nodes` and `asr_gateway`.

### Topics

- `/asr/runtime/audio/raw`
- `/asr/runtime/audio/preprocessed`
- `/asr/runtime/audio/segments`
- `/asr/runtime/results/partial`
- `/asr/runtime/results/final`
- `/asr/status/nodes`
- `/asr/status/sessions`

### Services

- `/asr/runtime/start_session`
- `/asr/runtime/stop_session`
- `/asr/runtime/reconfigure`
- `/asr/runtime/recognize_once`
- `/config/list_profiles`
- `/config/validate`

## Benchmark Surface

- `asr_benchmark_nodes` exposes benchmark and dataset actions/services over `asr_interfaces`.
- `scripts/run_benchmark_core.py` is the default local benchmark entrypoint.

## Compatibility Note

- `RecognizeOnce` remains the canonical one-shot ROS service.
- `ListBackends` remains a compatibility-named provider catalog service.
- `SetAsrBackend` remains in ROS IDL only for compatibility and is not part of the primary runbook.
