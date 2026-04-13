# asr_core

Shared provider-agnostic core primitives.

## Responsibilities
- Legacy core ASR request/response dataclasses (compatibility layer).
- Normalized result model for new architecture.
- Namespace/topic constants and ID helpers.
- Audio and language utilities.

## Boundary
No ROS node orchestration and no provider-specific branching logic.

## Mental Model
This package is intentionally boring. If a helper starts depending on ROS node lifecycle, provider-specific options, benchmark artifact layout, or browser/UI state, it probably does not belong here.

## Read This Package In This Order
1. `asr_core/models.py`
2. `asr_core/normalized.py`
3. `asr_core/audio.py`
4. `asr_core/namespaces.py`
5. `asr_core/ids.py`
