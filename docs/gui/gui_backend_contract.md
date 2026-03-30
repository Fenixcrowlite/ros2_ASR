# GUI Backend Contract (`asr_gateway`)

## Contract Principles
- GUI talks only to gateway HTTP API.
- Gateway maps requests to ROS2 services/actions and filesystem-backed artifacts.
- Responses include user-facing status and machine-readable fields.
- Credentials APIs return metadata only, never secret values.

## Base
- Host: `http://<gateway-host>:8088`
- Prefix: `/api`

## Health and System
- `GET /api/health`
  - Returns gateway uptime and service status.
- `GET /api/system/status`
  - Returns aggregated system status:
    - runtime status
    - benchmark status summary
    - providers readiness summary
    - alert list

## Runtime
- `GET /api/runtime/status`
  - Current runtime session/backend status.
- `POST /api/runtime/start`
  - Start runtime session with selected profiles.
- `POST /api/runtime/stop`
  - Stop session.
- `POST /api/runtime/reconfigure`
  - Reconfigure running session.
- `POST /api/runtime/recognize_once`
  - One-shot recognition.
- `GET /api/runtime/live`
  - Latest runtime snapshot for polling (status + recent outputs/events).

## Providers
- `GET /api/providers/catalog`
  - Provider catalog and capabilities matrix source.
- `GET /api/providers/profiles`
  - Provider profile summaries with credential linkage.
- `POST /api/providers/validate`
  - Validate provider profile.
- `POST /api/providers/test`
  - Smoke test provider profile (optional WAV).

## Profiles
- `GET /api/profiles`
  - List profile IDs grouped by type.
- `GET /api/profiles/{profile_type}`
  - List profile IDs for one type.
- `GET /api/profiles/{profile_type}/{profile_id}`
  - Get profile payload + file metadata.
- `PUT /api/profiles/{profile_type}/{profile_id}`
  - Save profile payload preserving custom fields.
- `POST /api/config/validate`
  - Validate profile using ROS config validation service.

## Datasets
- `GET /api/datasets`
  - Registry list.
- `GET /api/datasets/{dataset_id}`
  - Dataset detail + manifest stats + sample preview.
- `POST /api/datasets/import`
  - Import dataset via action.
- `POST /api/datasets/register`
  - Register existing manifest.
- `POST /api/datasets/validate_manifest`
  - Validate manifest structure and sample count.

## Benchmark
- `POST /api/benchmark/run`
  - Trigger benchmark action.
- `GET /api/benchmark/status/{run_id}`
  - Poll running status.
- `GET /api/benchmark/history`
  - List runs from artifact directories.

## Results
- `GET /api/results/overview`
  - Recent run summaries and quick stats.
- `GET /api/results/runs/{run_id}`
  - Full run detail (manifest, summary, mean metrics, artifacts refs).
- `POST /api/results/compare`
  - Compare selected runs and return metric table.
- `POST /api/results/export`
  - Export comparison summary to JSON/CSV/Markdown under `artifacts/exports`.

## Logs and Diagnostics
- `GET /api/diagnostics/health`
  - Subsystem health summary.
- `GET /api/diagnostics/issues`
  - Human-readable issues and suggested fixes.
- `GET /api/logs`
  - Filterable logs tail (`component`, `severity`, `limit`).
  - Returns `files`, `entry_count`, and per-entry metadata:
    `component`, `file`, `source`, `severity`, `timestamp`, `line_number`, `message`.

## Secrets
- `GET /api/secrets/refs`
  - Secret reference metadata list + validity checks.
- `POST /api/secrets/refs`
  - Create/update secret reference YAML metadata.
- `POST /api/secrets/validate`
  - Validate one ref readability/env requirements.
- `POST /api/secrets/link_provider`
  - Link secret ref to provider profile.

## Live Update Strategy
- Polling baseline:
  - Runtime page polls `/api/runtime/live`.
  - Benchmark page polls `/api/benchmark/status/{run_id}`.
  - Dashboard polls `/api/system/status`.
- API contract is compatible with future SSE/WebSocket upgrade.
