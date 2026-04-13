# asr_gateway

Gateway backend between GUI and ROS2/core subsystems.

## Responsibilities
- Validate profiles.
- Trigger runtime and benchmark flows via ROS services/actions.
- Provide stable API for GUI and automation.
- Expose datasets/results/secrets metadata.
- Aggregate diagnostics, logs, and benchmark/result history for GUI dashboards.

## Boundary rule
GUI should use this gateway instead of direct ROS graph/internal code access.

## Mental Model
- `api.py` is the HTTP boundary and request normalizer.
- `ros_client.py` is the ROS transport façade used by the HTTP layer.
- `result_views.py`, `log_views.py`, `runtime_assets.py`, and `secret_state.py` are read-model helpers for the browser UI.

## Read This Package In This Order
1. `asr_gateway/api.py`
2. `asr_gateway/ros_client.py`
3. `asr_gateway/result_views.py`
4. `asr_gateway/log_views.py`
5. `asr_gateway/runtime_assets.py`
6. `asr_gateway/secret_state.py`

That order mirrors the real control flow: HTTP request -> ROS interaction -> artifact/log projection for the UI.

## API Surface (Baseline)
- `/api/system/status`, `/api/dashboard`
- `/api/runtime/*` (status/start/stop/reconfigure/recognize/live/backends)
- `/api/providers/*` (catalog/profiles/validate/test)
- `/api/profiles/*` and `/api/config/validate`
- `/api/datasets/*` (list/detail/import/register/manifest-validate)
- `/api/benchmark/*` (run/status/history)
- `/api/results/*` (overview/run-detail/compare/export)
- `/api/diagnostics/*`, `/api/logs`, `/api/secrets/*`

## Runtime Environment Variables
- `ASR_GATEWAY_HOST` (default: `127.0.0.1`)
- `ASR_GATEWAY_PORT` (default: `8088`)
- `ASR_GATEWAY_RELOAD` (`1/true/on` enables uvicorn reload)
- `ASR_PROJECT_ROOT` (optional explicit repo root override for config/artifact path resolution)
