# Audit Phase 1: Inventory

## Repo shape

- ROS2/workspace packages under `ros2_ws/src`: 26
- Config/profile files under `configs/`: 87
- Test files under `tests/`: 152
- Frontend page modules under `web_ui/frontend/js/pages`: 9
- Documentation files under `docs/`: 162

## Primary entry points

- Operator shell:
  - `make run`
  - `make bench`
  - `make report`
  - `make web-gui`
- Canonical Python/HTTP:
  - `scripts/run_benchmark_core.py`
  - `asr_gateway.main`
  - `scripts/run_web_ui.sh`
- Canonical ROS2 launches:
  - `ros2_ws/src/asr_launch/launch/runtime_minimal.launch.py`
  - `ros2_ws/src/asr_launch/launch/gateway_with_runtime.launch.py`
  - `ros2_ws/src/asr_launch/launch/benchmark_single_provider.launch.py`
  - `ros2_ws/src/asr_launch/launch/benchmark_matrix.launch.py`

## Inventory by role

### Canonical platform core

- `ros2_ws/src/asr_core`
- `ros2_ws/src/asr_config`
- `ros2_ws/src/asr_datasets`
- `ros2_ws/src/asr_provider_base`
- `ros2_ws/src/asr_metrics`
- `ros2_ws/src/asr_storage`
- `ros2_ws/src/asr_reporting`

### Canonical execution layers

- `ros2_ws/src/asr_runtime_nodes`
- `ros2_ws/src/asr_benchmark_core`
- `ros2_ws/src/asr_benchmark_nodes`
- `ros2_ws/src/asr_gateway`
- `ros2_ws/src/asr_launch`
- `web_ui/frontend`

### Provider integrations

- `ros2_ws/src/asr_provider_whisper`
- `ros2_ws/src/asr_provider_vosk`
- `ros2_ws/src/asr_provider_azure`
- `ros2_ws/src/asr_provider_google`
- `ros2_ws/src/asr_provider_aws`

### Compatibility / legacy layers still present

- `ros2_ws/src/asr_benchmark`
- `ros2_ws/src/asr_ros`
- `ros2_ws/src/asr_backend_mock`
- `ros2_ws/src/asr_backend_whisper`
- `ros2_ws/src/asr_backend_vosk`
- `ros2_ws/src/asr_backend_azure`
- `ros2_ws/src/asr_backend_google`
- `ros2_ws/src/asr_backend_aws`
- `scripts/live_sample_eval.py`
- `configs/default.yaml`
- `configs/live_mic_whisper.yaml`

### Data / artifacts / operator state

- `datasets/`
- `artifacts/`
- `logs/`
- `results/`
- `models/`

## Classification summary

### Clearly used and architecturally central

- `asr_runtime_nodes`, `asr_gateway`, `asr_benchmark_core`, `asr_benchmark_nodes`
- `asr_provider_base` + provider profiles
- `asr_metrics.summary` and `asr_metrics.quality`
- `asr_storage`

### Used but structurally transitional

- `scripts/generate_report.py`
- `scripts/run_external_dataset_suite.py`
- `web_ui/frontend`
- `docs/benchmarking.md`

### High-noise / high-duplication zones

- `asr_benchmark` vs `asr_benchmark_core`
- `asr_ros` vs `asr_runtime_nodes`
- `asr_backend_*` vs `asr_provider_*`
- old flat config flow (`configs/default.yaml`) vs profile-driven config flow
- generated docs/graphs under `docs/arch`

## Inventory verdict

- The repository is no longer an unstructured prototype, but it still carries two architectural generations at once.
- The productive core is profile-driven and centered on normalized provider adapters, canonical benchmark artifacts, gateway APIs, and runtime nodes.
- The main repository risk is not missing functionality; it is duplicated execution paths that look equally valid while only one of them is the real target architecture.
