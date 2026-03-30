# Audit Phase 5 ROS2 Architecture

## Canonical ROS2-First Architecture

### Runtime nodes

- `audio_input_node`
- `audio_preprocess_node`
- `vad_segmenter_node`
- `asr_orchestrator_node`

### Benchmark ROS shell

- `benchmark_manager_node`

### Launch ownership

- `asr_launch` is the canonical bring-up package
- `asr_gateway` is the canonical HTTP/UI control surface

## Canonical Topics

- `/asr/runtime/audio/raw`
- `/asr/runtime/audio/preprocessed`
- `/asr/runtime/vad/activity`
- `/asr/runtime/audio/segments`
- `/asr/runtime/results/partial`
- `/asr/runtime/results/final`
- `/asr/status/nodes`
- `/asr/status/sessions`

## Canonical Services / Actions

### Runtime control

- `/asr/runtime/start_session`
- `/asr/runtime/stop_session`
- `/asr/runtime/reconfigure`
- `/asr/runtime/recognize_once`
- `/asr/runtime/get_status`
- `/asr/runtime/list_backends`
- `/config/list_profiles`
- `/config/validate`

### Runtime stage internals

- `/asr/runtime/audio/start_session`
- `/asr/runtime/audio/stop_session`
- `/asr/runtime/audio/reconfigure`
- `/asr/runtime/preprocess/reconfigure`
- `/asr/runtime/vad/reconfigure`

### Benchmark / datasets

- action `/benchmark/run_experiment`
- action `/datasets/import`
- service `/benchmark/get_status`
- service `/datasets/register`
- service `/datasets/list`

## Legacy ROS2 Surface

Still present:

- `asr_ros`
- old `/asr/recognize_once`
- old `/asr/set_backend`
- old `/asr/get_status`
- old `/asr/transcribe`
- old launch files `bringup.launch.py`, `demo.launch.py`, `benchmark.launch.py`

## Assessment

### Good in the canonical path

- transport and provider/business logic are separated better than in the legacy stack
- benchmark ROS node is a thin shell over benchmark core
- runtime node roles are explicit and easier to observe/debug

### Weak in the repository as a whole

- compatibility stack is still present in the same workspace and same interface package
- architecture docs and generated graphs therefore show both worlds
- new developers can still enter through the wrong runtime or the old direct benchmark runner

## Repair Performed

- `runtime_minimal.launch.py` now passes `runtime_profile` through to runtime stages instead of hardcoding file-mode audio settings.
- default operator benchmark path now runs through canonical benchmark core instead of the old flat benchmark runner.

## Remaining ROS2 Risks

1. `asr_ros` compatibility services still look like a viable primary runtime path.
2. Interface package still carries both canonical and legacy service/action semantics.
3. Namespace argument removal/rework is not complete across all launches; some operator expectations may still come from old docs rather than canonical runtime constants.

See also:

- `ROS2_RUNTIME_REFACTOR_NOTES.md`
- `TARGET_ARCHITECTURE_PROPOSAL.md`
