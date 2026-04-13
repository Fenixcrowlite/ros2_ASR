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

## Mental Model
- `audio_input_node` acquires or replays audio.
- `audio_preprocess_node` normalizes sample rate/channel/encoding.
- `vad_segmenter_node` groups chunks into speech segments for segmented mode.
- `asr_orchestrator_node` is the runtime control plane and the only node that should invoke provider adapters directly.

## Read This Package In This Order
1. `asr_runtime_nodes/asr_orchestrator_node.py`
2. `asr_runtime_nodes/audio_input_node.py`
3. `asr_runtime_nodes/audio_preprocess_node.py`
4. `asr_runtime_nodes/vad_segmenter_node.py`
5. `asr_runtime_nodes/converters.py`
6. `asr_runtime_nodes/transport.py`
