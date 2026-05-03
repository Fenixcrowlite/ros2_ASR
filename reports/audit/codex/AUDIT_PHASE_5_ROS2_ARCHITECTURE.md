# Audit Phase 5: ROS2 Architecture

## Canonical ROS2-first shape

### Runtime

- `audio_input_node`
- `audio_preprocess_node`
- `vad_segmenter_node`
- `asr_orchestrator_node`

### Benchmarking

- `asr_benchmark_nodes.benchmark_manager_node`
- benchmark launch files under `asr_launch`

### Transport/API bridge

- `asr_gateway` is intentionally not a ROS2 node package; it is the HTTP/operator bridge

## Strengths

- runtime orchestration is separated from provider adapters
- benchmark orchestration is separated from runtime path
- ROS2 message/service surface is explicit through `asr_interfaces`
- launch files under `asr_launch` are the canonical operational entrypoints

## Weaknesses

- legacy `asr_ros` package still duplicates runtime concerns
- legacy `asr_benchmark` package still exposes an older benchmark node around the flat runner
- gateway depends on both ROS2 client calls and direct core filesystem inspection, which is pragmatic but broad

## ROS2 verdict

- The repository is no longer “decorative ROS2”.
- It is ROS2-capable and reasonably layered, but not yet fully cleaned because the older node generation still exists beside the new one.
