# GUI Assessment

## Scope and Date
- Assessment date: 2026-03-12
- Repository: `/home/fenix/Desktop/ros2ws`
- Goal: evaluate current GUI/UX and define migration to architecture-safe, user-friendly GUI baseline for ROS2-first ASR platform.

## Current GUI State

### 1. `web_ui/` (new baseline, very minimal)
- Frontend: static `index.html` + `app.js` + `styles.css`.
- Backend: `asr_gateway` FastAPI in `ros2_ws/src/asr_gateway`.
- Existing capabilities:
  - Runtime start/stop/recognize once.
  - Basic profiles listing.
  - Dataset list.
  - Benchmark run trigger.
  - Artifacts listing.
  - Secret refs listing.
- Current UX quality:
  - Low information architecture depth.
  - No guided flows.
  - No structured forms/validation UX.
  - No clear operator vs engineer layering.
  - No diagnostics explanation layer.

### 2. `web_gui/` (legacy, feature-rich but architecture-misaligned)
- Contains independent FastAPI server and frontend with its own job orchestration.
- Strengths:
  - Many practical controls and file tools.
  - Rich runtime/benchmark execution options.
- Weaknesses relative to new target architecture:
  - Contains non-trivial orchestration logic coupled to GUI-specific backend.
  - Uses legacy config/job model not aligned to new `asr_*` package boundaries.
  - Not designed as strict gateway over `asr_runtime_nodes` + `asr_benchmark_nodes`.

## Existing Architectural Constraints
- Runtime and benchmark logic already separated in ROS2 packages.
- `asr_gateway` already provides ROS service/action bridge and can be expanded.
- Config model is profile-driven via `asr_config` and must remain source-of-truth.
- Secret refs are file/env based and must remain masked.
- Benchmark artifacts are reproducible in `artifacts/benchmark_runs/<run_id>/...` and should power Results UI.

## UX Problems to Solve
- Lack of clear "what to do next" guidance for first-time users.
- No central status narrative (gateway/runtime/provider/benchmark health).
- No run builder UX for benchmark (user has to fill raw fields mentally).
- No profile management UX beyond raw listing.
- Limited error explanation and remediation hints.
- Credentials experience is metadata-only but not workflow-oriented.

## Target Interface Model
- One architecture-safe GUI over `asr_gateway` API.
- Top navigation:
  - Dashboard
  - Runtime
  - Providers
  - Profiles
  - Datasets
  - Benchmark
  - Results
  - Logs & Diagnostics
  - Secrets
- Progressive disclosure:
  - Basic controls first.
  - Advanced details in expandable panels.
- Live behavior by polling abstraction:
  - Runtime status polling.
  - Benchmark status polling.
  - Diagnostics refresh.

## Migration Strategy
1. Keep `web_gui/` as legacy compatibility module (no destructive removal now).
2. Make `web_ui/` + `asr_gateway` the canonical GUI path for new architecture.
3. Expand gateway contract first, then rebuild frontend around task flows.
4. Preserve config/profile file model (GUI edits YAML through gateway, not replacing file architecture).
5. Keep credentials masked and reference-based only.
6. Mark legacy GUI in docs as deprecated for future ROS2-first unified UX.

## Reuse Map
- Reuse:
  - `asr_gateway` FastAPI base.
  - ROS service/action clients in `ros_client.py`.
  - `asr_config` profile resolution and validation.
  - `asr_datasets` registry + manifest tools.
  - `asr_storage` and benchmark artifacts.
- Refactor/extend:
  - Gateway API surface and response models.
  - Frontend IA, patterns, and components.
- Keep as legacy/deprecated:
  - `web_gui/` workflow backend and old static UI.
