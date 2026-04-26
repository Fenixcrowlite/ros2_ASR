# Run Guide

## Runtime

- Build: `make build`
- Full local UI stack: `make up`
- Runtime-only stack: `make up-runtime`

Profiles:

- runtime profile: `configs/runtime/*.yaml`
- provider profile: `configs/providers/*.yaml`

Examples:

```bash
make up-runtime RUNTIME_PROFILE=default_runtime PROVIDER_PROFILE=providers/whisper_local
make up-runtime RUNTIME_PROFILE=huggingface_local_runtime PROVIDER_PROFILE=providers/huggingface_local
```

## Benchmark

- Run benchmark: `make bench`
- Render report: `make report`

## Validation

- Unit tests: `make test-unit`
- ROS tests: `make test-ros`
- Colcon tests: `make test-colcon`

## Archive

Historical runtime scripts, flat configs, and compatibility packages were moved under `legacy/` and are not part of the default production runbook.
