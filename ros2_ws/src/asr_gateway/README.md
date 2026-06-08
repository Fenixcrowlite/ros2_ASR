# asr_gateway

FastAPI gateway between the browser UI/automation clients and the ROS2/core
ASR subsystems.

## Purpose

The gateway is the stable HTTP boundary of the project. Frontend code and
external automation should talk to this package instead of:

- calling ROS services/actions directly
- reading artifact directories directly
- parsing logs/config files directly

It normalizes the ROS side, filesystem state, provider catalog, benchmark
artifacts, runtime assets, and secret status into one HTTP API.

## Main Responsibilities

- Validate profiles and free-form payloads before they reach ROS nodes.
- Trigger runtime and benchmark flows via ROS services/actions.
- Expose provider catalog, preset, and capability metadata.
- Expose datasets, benchmark history, result comparison, and exports.
- Project logs, diagnostics, secret status, and runtime assets for the UI.
- Serve the web frontend in local development flows.

## Key Modules

- `asr_gateway/api.py`: FastAPI app, request models, and route handlers.
- `asr_gateway/ros_client.py`: synchronous ROS client façade used by the HTTP
  layer.
- `asr_gateway/result_views.py`: benchmark history/detail/compare read models.
- `asr_gateway/log_views.py`: logical log discovery and tail helpers.
- `asr_gateway/runtime_assets.py`: runtime sample upload/list/read helpers.
- `asr_gateway/secret_state.py`: provider secret-status inspection.
- `asr_gateway/main.py`: `uvicorn` entry point.

Console entry point:

- `asr_gateway_server = asr_gateway.main:main`

## Mental Model

HTTP request
-> validate/normalize payload in `api.py`
-> call ROS or local helpers
-> project artifacts/logs/secrets into browser-friendly JSON
-> return a stable response for the frontend

## API Surface (Baseline)

- `/api/system/status`, `/api/dashboard`
- `/api/runtime/*` for runtime control and live recognition
- `/api/providers/*` for provider catalog, profiles, validation, and checks
- `/api/profiles/*` and `/api/config/validate`
- `/api/datasets/*` for dataset list/detail/import/validation
- `/api/benchmark/*` for run/start/status/history
- `/api/results/*` for history, detail, compare, and export
- `/api/diagnostics/*`, `/api/logs`, `/api/secrets/*`

## Runtime Environment Variables

- `ASR_GATEWAY_HOST` (default: `127.0.0.1`)
- `ASR_GATEWAY_PORT` (default: `8088`)
- `ASR_GATEWAY_RELOAD` (`1/true/on` enables `uvicorn` reload)
- `ASR_PROJECT_ROOT` to override root path detection for configs/artifacts

## Boundary Rules

- Frontend code should not bypass the gateway to inspect ROS or artifact trees.
- ROS message orchestration remains in `asr_runtime_nodes` and
  `asr_benchmark_nodes`.
- Benchmark execution logic remains in `asr_benchmark_core`.
