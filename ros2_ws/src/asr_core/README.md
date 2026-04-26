# asr_core

Shared low-level primitives for the canonical ASR stack.

## Responsibilities

- common IDs and topic namespace constants
- audio helpers
- normalized result model support
- request/response dataclasses retained for provider-internal compatibility code
- generic utilities that must stay independent of ROS nodes, gateway handlers, and benchmark orchestration

## Key Modules

- `asr_core/ids.py`
- `asr_core/namespaces.py`
- `asr_core/audio.py`
- `asr_core/normalized.py`
- `asr_core/models.py`
- `asr_core/ros_parameters.py`
- `asr_core/shutdown.py`

## Boundary

`asr_core` does not own provider selection, ROS node orchestration, HTTP routes, benchmark planning, or archived compatibility package wiring.
