# asr_ros (Legacy)

Legacy ROS2 runtime package retained for backward compatibility with the older
single-server ASR workflow.

## Status

Primary runtime development has moved to:

- `asr_runtime_nodes`
- `asr_launch`

New features should generally target the newer runtime pipeline unless the goal
is explicit compatibility.

## Main Components

- `asr_ros/asr_server_node.py`: legacy all-in-one ASR server node exposing
  services, action, and live chunk subscription.
- `asr_ros/audio_capture_node.py`: legacy microphone/file audio source node.
- `asr_ros/asr_text_output_node.py`: simple text subscriber/output node.
- `asr_ros/converters.py`: conversions from core models to ROS messages.
- `launch/bringup.launch.py`, `launch/demo.launch.py`,
  `launch/benchmark.launch.py`: legacy launch flows.

## Architecture Difference vs New Runtime

The legacy path concentrates more behavior into fewer nodes. The modern stack
splits the runtime into dedicated stages:

- audio input
- preprocessing
- VAD segmentation
- orchestrator/provider selection

That newer split is easier to observe, benchmark, and evolve.

## When This Package Is Still Useful

- Legacy tests and demos.
- Migration work where older launch files must keep working.
- Comparing behavior against the newer runtime stack.
