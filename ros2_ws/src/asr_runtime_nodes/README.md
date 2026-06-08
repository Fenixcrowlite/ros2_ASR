# asr_runtime_nodes

ROS2-first runtime pipeline for live and replayed ASR.

## Purpose

This package is the modern runtime path of the repository. It decomposes the
runtime into focused nodes instead of one monolithic server:

- audio acquisition
- preprocessing
- VAD segmentation
- orchestration and provider inference

That separation makes the system easier to observe, reconfigure, benchmark, and
replace stage by stage.

## Nodes

- `audio_input_node`:
  file/microphone source -> `AudioChunk`
- `audio_preprocess_node`:
  resample, mono mix, normalize, and transport metadata updates
- `vad_segmenter_node`:
  speech activity detection and segment extraction
- `asr_orchestrator_node`:
  runtime control plane, provider selection, inference, result publishing, and
  runtime services

Console entry points:

- `audio_input_node = asr_runtime_nodes.audio_input_node:main`
- `audio_preprocess_node = asr_runtime_nodes.audio_preprocess_node:main`
- `vad_segmenter_node = asr_runtime_nodes.vad_segmenter_node:main`
- `asr_orchestrator_node = asr_runtime_nodes.asr_orchestrator_node:main`

## Supporting Modules

- `asr_runtime_nodes/converters.py`: convert normalized provider results into
  ROS interface messages.
- `asr_runtime_nodes/transport.py`: encode/decode transport metadata stored in
  ROS headers.

## Runtime Flow

`audio_input_node`
-> raw audio topic
-> `audio_preprocess_node`
-> preprocessed audio topic
-> `vad_segmenter_node`
-> speech segments
-> `asr_orchestrator_node`
-> partial/final ASR results and runtime state

## Responsibilities

- Resolve runtime and provider profiles.
- Support segmented and provider-stream processing modes.
- Publish node status and session status topics.
- Keep provider adapter invocation isolated to the orchestrator node.
- Emit runtime observability traces and resource samples when enabled.

## Boundary Rules

- Runtime-only concerns belong here.
- Benchmark scheduling does not belong here.
- Browser/API shaping does not belong here.

## Read This Package In This Order

1. `asr_runtime_nodes/asr_orchestrator_node.py`
2. `asr_runtime_nodes/audio_input_node.py`
3. `asr_runtime_nodes/audio_preprocess_node.py`
4. `asr_runtime_nodes/vad_segmenter_node.py`
5. `asr_runtime_nodes/converters.py`
6. `asr_runtime_nodes/transport.py`
