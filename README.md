# Universal ASR for ROS2 Jazzy

Modular production-oriented ASR workspace for ROS2 Jazzy.

## Canonical Stack

- runtime: `asr_launch` + `asr_runtime_nodes`
- providers: `asr_provider_base` + `asr_provider_*`
- benchmark: `asr_benchmark_core` + `asr_benchmark_nodes`
- operator surface: `asr_gateway` + `web_ui`
- shared layers: `asr_core`, `asr_config`, `asr_datasets`, `asr_metrics`, `asr_storage`, `asr_reporting`, `asr_interfaces`

Archived compatibility packages, flat configs, and historical docs now live under `legacy/`.

## Main Commands

```bash
make setup
make build
make test-unit
make test-ros
make test-colcon
make bench
make report
make up
make up-runtime
```

## Docs

- `docs/architecture.md`
- `docs/architecture/provider_model.md`
- `docs/run_guide.md`
- `docs/benchmarking.md`
- `docs/interfaces.md`
- `docs/newbie_guide.md`
