# web_ui

New GUI baseline split:

- `frontend/` static SPA control center (modular JS pages + shared API/UI layer).
- `backend/` gateway integration notes (`asr_gateway` package provides API).

Legacy GUI remains in `web_gui/` and is marked as migration compatibility layer.

## Frontend structure
- `frontend/index.html` - app shell and page containers.
- `frontend/styles.css` - design system tokens + responsive layout.
- `frontend/js/api.js` - typed endpoint wrappers for gateway calls.
- `frontend/js/ui.js` - reusable rendering/util helpers.
- `frontend/js/pages/*.js` - task-oriented page modules:
  - dashboard/runtime/providers/profiles/datasets/benchmark/results/logs/secrets.
