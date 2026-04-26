# Newbie Guide

## Start Here

The active production path is:

1. `asr_launch`
2. `asr_runtime_nodes`
3. `asr_provider_base` + `asr_provider_*`
4. `asr_benchmark_core` + `asr_benchmark_nodes`
5. `asr_gateway` + `web_ui`

## Read In This Order

1. `docs/architecture.md`
2. `docs/architecture/provider_model.md`
3. `ros2_ws/src/asr_runtime_nodes/README.md`
4. `ros2_ws/src/asr_benchmark_core/README.md`
5. `ros2_ws/src/asr_gateway/README.md`

## Important Rules

- Use profiles from `configs/runtime`, `configs/providers`, `configs/benchmark`, `configs/datasets`, `configs/metrics`.
- Treat top-level `legacy/` as archive/reference only.
- For new integrations or fixes, extend `asr_provider_*`, not archived compatibility packages.
- For runtime control, start from `asr_launch` and `asr_gateway`, not from historical archived runbooks.
