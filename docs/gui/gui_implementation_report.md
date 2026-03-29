# GUI Implementation Report

## Date and Scope
- Date: 2026-03-12
- Scope: user-friendly GUI baseline for modular ROS2-first ASR platform.
- Main targets:
  - human-centered navigation and workflows;
  - architecture-safe gateway integration;
  - runtime + benchmark usability;
  - diagnostics and explainability baseline.

## State Before Changes
- `web_ui/frontend` existed as a minimal static panel with limited controls.
- `asr_gateway` provided only a narrow API subset.
- Legacy `web_gui/` had rich features but was not aligned with the new package boundaries and gateway-first model.
- After the migration milestone, the legacy `web_gui/` was removed and the missing operator tooling was folded into `web_ui` + `asr_gateway`.
- Missing UX artifacts:
  - no clear IA docs;
  - no design system;
  - no explicit backend contract for GUI.

## Main Problems Addressed
- Missing task-oriented IA and progressive disclosure.
- Weak status explainability (system/runtime/benchmark).
- Limited profile/provider/dataset management UX.
- Benchmark flow lacked builder/progress/history UX.
- Diagnostics lacked issue-to-action mapping.
- Secret refs UX lacked end-to-end workflow in the new GUI baseline.

## Documentation Implemented (`docs/gui/*`)
- `gui_assessment.md`
- `information_architecture.md`
- `design_system.md`
- `ui_patterns.md`
- `user_flows.md`
- `gui_backend_contract.md`
- `gui_implementation_report.md` (this file)
- `README.md` (index)

## Backend/Gateway Changes

### Extended API surface (`asr_gateway.api`)
- Added system/dashboard endpoints:
  - `/api/system/status`, `/api/dashboard`
- Runtime endpoints:
  - `/api/runtime/status`, `/api/runtime/live`, `/api/runtime/backends`
  - existing start/stop/reconfigure/recognize endpoints retained and integrated with runtime event/result cache
- Providers endpoints:
  - `/api/providers/catalog`, `/api/providers/profiles`, `/api/providers/validate`, `/api/providers/test`
- Profiles endpoints:
  - grouped listing, detailed profile read/save, validation integration
- Datasets endpoints:
  - registry list + detail preview
  - import/register/manifest validation
- Benchmark endpoints:
  - asynchronous run trigger + in-memory run state
  - status and history
- Results endpoints:
  - overview, run detail, comparison, export
- Diagnostics/logging endpoints:
  - health summary, issues feed, filtered log feed
- Secrets endpoints:
  - refs listing with validation metadata
  - upsert/validate/link-provider flows
- Artifact endpoint expanded with comparisons/exports.

### ROS client extensions (`asr_gateway.ros_client`)
- Added runtime status retrieval (`GetAsrStatus`).
- Added backend listing (`ListBackends`).
- Extended benchmark run call to pass explicit `run_id`.

### Robust path resolution
- Gateway now auto-detects project root (supports launch from repo root or `ros2_ws/`).
- Optional override via `ASR_PROJECT_ROOT`.

## Frontend Changes (`web_ui/frontend`)

### Architecture
- Rebuilt as modular static SPA using ES modules:
  - `js/api.js` (typed API wrappers)
  - `js/state.js` (predictable state container)
  - `js/ui.js` (reusable rendering/status/toast/table helpers)
  - `js/pages/*.js` (page-level containers)
  - `js/app.js` (routing/polling bootstrap)

### Pages implemented
- Dashboard
- Runtime
- Providers
- Profiles
- Datasets
- Benchmark
- Results
- Logs & Diagnostics
- Secrets

### UX baselines implemented
- Clear top-level navigation and page hierarchy.
- Helper text for non-obvious entities and actions.
- Basic + advanced layering (guided profile edit + raw JSON editor).
- Inline feedback blocks and toast notifications.
- Empty states with next-step guidance.
- Status badges for health/state readability.
- Polling-driven live UX for runtime and benchmark state.

## Supported User Flows (implemented baseline)
- Quick runtime start/stop plus whole-file transcription.
- Provider profile validation and smoke test.
- Profile browsing, guided edit, advanced raw edit, save, validate.
- Dataset import/register/manifest validation + preview.
- Benchmark run builder and run status polling.
- Result run detail + multi-run comparison + export.
- Diagnostics issue feed and filtered logs.
- Secret ref create/validate and provider-profile linking.

## Architecture Alignment
- GUI relies on gateway APIs and does not access ROS graph directly.
- Profile management preserves file-driven config model.
- Secret handling remains reference-based and masked.
- Benchmark/result views are backed by real artifact directories and run manifests.
- Repository root now exposes a single active browser UI tree: `web_ui/`.

## What Is Working End-to-End
- New frontend serves and renders all required top-level pages.
- Gateway endpoints respond for status/profile/provider/dataset/benchmark/result/diagnostics/secrets workflows.
- Benchmark submission supports queued/running/completed lifecycle in gateway state and can be polled.
- Results and exports are generated from actual artifact data.

## Limitations / Known Gaps
- Runtime transcription live feed is currently based on gateway-visible recent outputs (service-driven path), not full ROS topic subscription stream.
- Provider status validity depends on runtime availability of provider packages/credentials in current environment.
- Frontend build-time JS lint/type checks were not executed because Node.js is not available in this environment.
- Benchmark progress granularity depends on underlying ROS benchmark status reporting.

## Future Work
1. Add SSE/WebSocket channel for runtime partial/final stream and benchmark progress events.
2. Add richer charting for results (WER/CER/latency visual plots).
3. Extend profile editor schemas with per-type advanced validation hints and form widgets.
4. Add role-aware UX presets (operator vs engineer mode toggle).
5. Add diagnostic deep-links from issue items directly to remediation forms.
