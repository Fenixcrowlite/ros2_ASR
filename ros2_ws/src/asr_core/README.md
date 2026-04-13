# asr_core

Provider-agnostic primitives shared by legacy ROS nodes, the new runtime stack,
provider adapters, the benchmark subsystem, and the gateway.

## Why This Package Exists

`asr_core` is the lowest Python layer in the workspace. It contains only
concepts that stay stable regardless of which provider is active, whether audio
is processed live or offline, and whether the caller is a ROS node, a benchmark
runner, or the HTTP gateway.

If a helper starts depending on ROS node lifecycle, FastAPI request models,
artifact storage layout, or provider-specific SDK objects, it should usually
move out of `asr_core`.

## Main Responsibilities

- Define legacy request/response models used by compatibility backends.
- Define the normalized ASR result model used by the modern runtime pipeline.
- Centralize topic names, ID generation helpers, and simple runtime utilities.
- Provide audio, config, language, and shutdown helpers that other packages can
  reuse without importing each other in circles.

## Key Modules

- `asr_core/models.py`: legacy backend-facing dataclasses such as
  `AsrRequest`, `AsrResponse`, and `AsrTimings`.
- `asr_core/normalized.py`: canonical provider-neutral result model used by the
  new provider adapter architecture.
- `asr_core/audio.py`: WAV inspection, PCM conversion, chunking, and small audio
  normalization helpers reused by runtime and benchmark code.
- `asr_core/backend.py`: abstract legacy backend contract.
- `asr_core/factory.py`: registry/factory for legacy backend creation.
- `asr_core/namespaces.py`: shared topic/service namespace constants.
- `asr_core/ids.py`: deterministic ID helpers for sessions, requests, and runs.
- `asr_core/ros_parameters.py`: safe parameter coercion helpers for ROS nodes.
- `asr_core/shutdown.py`: common shutdown/spin helpers used by multiple nodes.

## Data Model Layers

- Legacy path:
  `AsrRequest` -> legacy backend -> `AsrResponse`
- Modern path:
  `ProviderAudio` in `asr_provider_base` -> provider adapter ->
  `NormalizedAsrResult`

Both models live side by side because the repository currently supports a
compatibility layer (`asr_ros`, `asr_backend_*`) and a newer runtime/provider
stack (`asr_runtime_nodes`, `asr_provider_*`).

## Used By

- `asr_ros` and `asr_backend_*` through the legacy request/response model.
- `asr_runtime_nodes`, `asr_provider_base`, and `asr_provider_*` through the
  normalized result model and utility helpers.
- `asr_benchmark_core`, `asr_gateway`, and `asr_storage` through IDs, audio
  helpers, and general-purpose shared types.

## Boundary Rules

- No ROS node creation or executor logic.
- No FastAPI/Pydantic code.
- No provider SDK initialization.
- No artifact persistence rules.
- No benchmark orchestration state.

## Read This Package In This Order

1. `asr_core/models.py`
2. `asr_core/normalized.py`
3. `asr_core/audio.py`
4. `asr_core/namespaces.py`
5. `asr_core/ids.py`
6. `asr_core/ros_parameters.py`
