# ROS2 Runtime Refactor Notes

## Completed

- Repaired `runtime_minimal.launch.py` so that runtime profile data reaches:
  - `audio_input_node`
  - `audio_preprocess_node`
  - `vad_segmenter_node`
- This removed a false split where launch defaults silently overrode runtime profile audio configuration.

## Current Runtime Layering

- transport and stage control: `asr_runtime_nodes`
- provider resolution: `asr_provider_base`
- provider execution: `asr_provider_*`
- result normalization: provider adapters + `asr_core.normalized`
- HTTP/UI bridge: `asr_gateway`

## Deferred

1. Quarantine `asr_ros` more aggressively or move it to an explicit compatibility zone.
2. Audit all launch defaults for remaining decorative arguments.
3. Add canonical ROS2 smoke tests for the new runtime stack that are independent of legacy `asr_ros`.
