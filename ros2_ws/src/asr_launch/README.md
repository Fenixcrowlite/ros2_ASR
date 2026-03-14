# asr_launch

Launch package for modular deployment scenarios.

## Launch files
- `runtime_minimal.launch.py`
- `runtime_streaming.launch.py`
- `benchmark_single_provider.launch.py`
- `benchmark_matrix.launch.py`
- `gateway_with_runtime.launch.py`
- `full_stack_dev.launch.py`

## New GUI startup
- Full stack with new `web_ui` via gateway:
  - `ros2 launch asr_launch full_stack_dev.launch.py gateway_host:=0.0.0.0 gateway_port:=8088`
- Runtime + gateway only:
  - `ros2 launch asr_launch gateway_with_runtime.launch.py gateway_host:=127.0.0.1 gateway_port:=8088`

The `web_ui` frontend is served by `asr_gateway` at `/` (for example: `http://localhost:8088`).
