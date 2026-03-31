# Action Plan

Audit date: `2026-03-31`
Refresh after remediation: `2026-03-31`

## Completed in this pass

| Work item | Status | Validation |
|---|---|---|
| Canonical vs legacy workflow enforcement | done | `make build`, `make test-unit`, `make test-ros`, `make test-colcon` |
| Canonical Python import-path isolation | done | `pytest -q tests/integration/test_source_runtime_env.py` |
| Runtime payload and validator correctness fixes | done | targeted unit tests + `make test-unit` |
| Persistent gateway ROS bridge | done | `pytest -q tests/unit/test_gateway_ros_client.py` |
| Honest provider readiness semantics | done | `pytest -q tests/api/test_gateway_api.py::test_provider_catalog_distinguishes_ready_and_degraded_profiles` |
| Live runtime trace export for segmented and provider-stream flows | done | `pytest -q tests/unit/test_runtime_observability_export.py` |
| Model load / warm-cold metrics | done | `pytest -q tests/component/test_provider_manager.py`, benchmark rerun |
| Dependency split + CI security/failure-artifact upgrades | done | `make security-scan`, `bash scripts/secret_scan.sh`, workflow update |
| Legacy benchmark manifest determinism | done | `pytest -q tests/unit/test_dataset.py` |

## Recommended next patch set

1. Emit resolved-config/session-manifest artifacts for long-lived runtime sessions at session start/stop.
2. Expand docs/wiki canonical-vs-legacy banners outside the root README.
3. Add deeper system profiling if peak/over-time CPU/GPU evidence becomes necessary.
4. Add DDS-native queue/backpressure instrumentation only if sequence-gap telemetry proves insufficient.
