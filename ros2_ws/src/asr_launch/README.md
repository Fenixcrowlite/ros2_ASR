# asr_launch

Launch scenarios for the modern runtime, benchmark, gateway, and full-stack
development topology.

## Purpose

This package is the operational entry layer for ROS users. Instead of manually
starting each node, operators and developers can choose a launch file that
matches the desired stack shape.

## Launch Files

- `runtime_minimal.launch.py`:
  audio input + preprocess + VAD + orchestrator
- `runtime_streaming.launch.py`:
  runtime pipeline tuned for microphone/stream-like behavior
- `benchmark_single_provider.launch.py`:
  benchmark manager for one-provider benchmark jobs
- `benchmark_matrix.launch.py`:
  benchmark manager for provider-matrix experiments
- `gateway_with_runtime.launch.py`:
  runtime pipeline plus FastAPI gateway
- `full_stack_dev.launch.py`:
  runtime + gateway + benchmark manager

## Shared Helpers

- `asr_launch/launch_env.py`: environment propagation for launched nodes
- `asr_launch/launch_guard.py`: protection against conflicting managed stacks

## Common Launch Arguments

Depending on the chosen launch file, typical arguments include:

- `runtime_profile`
- `provider_profile`
- `configs_root`
- `artifacts_root`
- `gateway_host`
- `gateway_port`
- `input_mode`

## Typical Usage

Full stack with UI served by the gateway:

```bash
ros2 launch asr_launch full_stack_dev.launch.py gateway_host:=0.0.0.0 gateway_port:=8088
```

Runtime plus gateway only:

```bash
ros2 launch asr_launch gateway_with_runtime.launch.py gateway_host:=127.0.0.1 gateway_port:=8088
```

The `web_ui` frontend is served by `asr_gateway` at `/`, for example
`http://localhost:8088`.
