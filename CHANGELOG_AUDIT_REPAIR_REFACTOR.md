# Changelog Audit Repair Refactor

Date: 2026-03-30

## Code Repairs

### Config resolution

- activated deployment-scoped defaults for runtime and benchmark profile resolution
- added tests proving scoped defaults now apply without leaking scaffold keys into resolved payload

### Provider construction

- activated provider profile `adapter` field
- added test covering explicit adapter-path instantiation without registry pre-registration

### Benchmark core

- benchmark profile `execution_mode` now participates in run planning
- benchmark artifact save flags now control raw/normalized output persistence
- added `scripts/run_benchmark_core.py` as a canonical benchmark-core CLI
- `scripts/run_benchmarks.sh` and `make bench` now run through canonical `asr_benchmark_core`
- canonical benchmark runs now export compatibility `results/benchmark_results.*` artifacts from core outputs
- canonical benchmark runs now publish `results/latest_benchmark_summary.json` and `results/latest_benchmark_run.json`
- `make report` now renders from canonical benchmark summary JSON instead of depending on the flat legacy artifact as its source of truth
- `scripts/generate_report.py` now accepts canonical benchmark `summary.json` objects in addition to legacy flat result lists
- added tests for:
  - profile-driven streaming execution mode
  - artifact save toggle behavior
  - canonical benchmark CLI export behavior
  - canonical summary report rendering

### Runtime launch fidelity

- removed hardcoded audio overrides from `runtime_minimal.launch.py`
- minimal launch now follows runtime profile values end-to-end

### Metric semantics

- repaired empty-reference quality support semantics
- repaired reliability summary semantics so rate metrics use numerator/denominator/value
- introduced explicit `cost_totals` in benchmark summaries
- removed fake summary-level `resource_metrics` aggregation
- added regression assertions for:
  - explicit invalid-reference handling
  - rate-statistics behavior
  - cost total propagation through benchmark summaries

## Validation Performed

Executed and passing:

- `tests/unit/test_config_loader.py`
- `tests/component/test_provider_manager.py`
- `tests/component/test_benchmark_orchestrator.py`
- `tests/unit/test_metric_engine_baseline.py`
- `tests/unit/test_metric_summary.py`
- `tests/unit/test_quality.py`
- `tests/unit/test_launch_defaults.py`
- `tests/integration/test_cli_flows.py`
- `tests/unit/test_gateway_result_views.py`

## Not Completed In This Pass

- wiring of `configs/gui/default_gui.yaml` into gateway bootstrap
- physical movement of legacy packages/scripts into a separate compatibility zone
- formal full-pipeline latency metric design beyond provider-result latency
