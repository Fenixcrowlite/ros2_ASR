# asr_runtime_nodes

Runtime ROS2-first ASR pipeline nodes.

## Nodes
- `audio_input_node`: file/mic source -> `AudioChunk`.
- `audio_preprocess_node`: resample/mono/normalize.
- `vad_segmenter_node`: speech activity + segment extraction.
- `asr_orchestrator_node`: provider selection, inference, normalized result publishing, runtime services.

## Boundaries
- Runtime-only concerns.
- No benchmark orchestration logic.
