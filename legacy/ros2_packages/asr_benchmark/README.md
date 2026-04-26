# asr_benchmark (Legacy)

Legacy benchmark package retained for backward compatibility with older launch
files and scripts.

## Status

New development should target:

- `asr_benchmark_core`
- `asr_benchmark_nodes`

## What Lives Here

- `asr_benchmark/benchmark_node.py`: older ROS benchmark node implementation.
- `asr_benchmark/runner.py`: older direct benchmark execution entry point.
- `asr_benchmark/dataset.py`: legacy dataset manifest reader helpers.
- `asr_benchmark/noise.py`: legacy noise helper.
- `launch/benchmark.launch.py`: legacy benchmark launch file.

## Why It Still Exists

- Compatibility with scripts or tests that still import the old package.
- Migration buffer while the modern benchmark stack becomes the only path.

## Boundary

Do not add new benchmark features here unless the goal is explicit backward
compatibility.
