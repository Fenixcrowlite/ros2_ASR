# Audit Phase 7 Cleanup Plan

## Completed In This Pass

1. Activated deployment-scoped defaults for runtime/benchmark profile resolution.
2. Activated provider profile `adapter` field.
3. Activated benchmark profile `execution_mode`.
4. Activated benchmark raw/normalized artifact toggles.
5. Removed hardcoded audio overrides from `runtime_minimal.launch.py`.
6. Repaired misleading empty-reference quality semantics.
7. Added regression tests for the repaired behavior.
8. Added `scripts/run_benchmark_core.py` and moved `make bench` onto canonical benchmark core.
9. Moved `make report` onto canonical benchmark summary JSON.

## Cleanup Matrix Summary

### Keep as canonical

- `asr_runtime_nodes`
- `asr_provider_base`
- `asr_provider_*`
- `asr_benchmark_core`
- `asr_benchmark_nodes`
- `asr_gateway`
- `asr_config`
- `asr_storage`
- `asr_metrics`
- `asr_datasets`

### Keep as compatibility / legacy

- `asr_ros`
- `asr_benchmark`
- `asr_backend_*`
- `configs/default.yaml`

### Keep as canonical bridge utilities

- `scripts/run_benchmark_core.py`
- `scripts/run_benchmarks.sh`
- `scripts/generate_report.py`

### Defer structural movement

Physical moves into `legacy/` were intentionally deferred because:

- tests still cover compatibility modules directly
- docs and generated architecture artifacts still reference them
- removing them in the same pass would be higher-risk than the semantic repairs completed here

## Recommended Next Cleanup Actions

1. Introduce an explicit `compatibility/` or `legacy/` zone for old runtime/benchmark packages and scripts.
2. Wire or delete `configs/gui/default_gui.yaml`.
3. Decide whether tracked sample outputs under `results/live_sample_smoke*` belong in source control or should move to a separate evidence bundle.
4. Quarantine or de-emphasize direct `python -m asr_benchmark.runner` usage in docs and operator paths.
