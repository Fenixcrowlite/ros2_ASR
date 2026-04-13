# web_ui

Gateway-first control center for the active browser UI.

This is the only active browser UI in the repository. The historical
`web_gui/` tree has been removed after migration into `web_ui` + `asr_gateway`.

Structure:

- `frontend/` static SPA control center (modular JS pages + shared API/UI layer).
- `backend/` gateway integration notes (`asr_gateway` package provides API).

## Frontend structure
- `frontend/index.html` - app shell and page containers.
- `frontend/styles.css` - design system tokens + responsive layout.
- `frontend/js/api.js` - typed endpoint wrappers for gateway calls.
- `frontend/js/ui.js` - reusable rendering/util helpers.
- `frontend/js/pages/*.js` - task-oriented page modules:
  - dashboard/runtime/providers/profiles/datasets/benchmark/results/logs/secrets.

## Included operator tooling
- Runtime start/stop/reconfigure plus whole-file transcription.
- Project sample catalog with drag-and-drop WAV upload.
- Runtime noise-variant generation for quick robustness checks.
- Provider/profile/dataset/benchmark/results workflows through `asr_gateway`.
- Diagnostics page with log filters and environment preflight.
- Secrets page for AWS SSO login status, Google JSON upload, and Azure env management.
- Contextual help via collapsible guides, field legends, and browser-native datalist suggestions for common languages, paths, and provider profiles.

Noise-robustness controls:

- Runtime page: choose a synthetic noise family and generate preset or custom SNR variants from one WAV sample.
- Benchmark page: scenario-aware defaults automatically switch between clean-only and multi-level robustness sweeps.
- Results page: stored runs expose `noise_mode`, `noise_level`, and per-noise summaries so robustness comparisons are visible in the UI.

Runtime page semantics:

- `Start Live Runtime` starts the live ROS runtime pipeline. In file-mode, the WAV is replayed as a paced audio stream and results arrive per segment.
- `Transcribe Whole File` sends the selected WAV through one direct `recognize_once` request and returns one whole-file transcript without keeping runtime active.
- Long WAV files are better suited for `Transcribe Whole File` when the goal is one readable transcript instead of segment-level pipeline inspection.

## Read This Package In This Order
1. `frontend/js/app.js`
2. `frontend/js/state.js`
3. `frontend/js/api.js`
4. `frontend/js/ui.js`
5. task pages:
   - `frontend/js/pages/runtime.js`
   - `frontend/js/pages/benchmark.js`
   - `frontend/js/pages/results.js`
   - `frontend/js/pages/secrets.js`

The browser code is intentionally thin. If a page starts containing transport, filesystem, or ROS-specific behavior, the owning logic usually belongs in `asr_gateway` instead.
