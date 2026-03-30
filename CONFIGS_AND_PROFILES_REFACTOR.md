# Configs And Profiles Refactor

## Completed In This Pass

1. `resolve_profile` now applies deployment-scoped defaults to the relevant profile family instead of leaving them as decorative nested payload.
2. `ProviderManager` now respects explicit provider `adapter` paths from provider profiles.
3. Benchmark core now seeds `execution_mode` from the benchmark profile itself.
4. Benchmark core now honors `save_raw_outputs` and `save_normalized_outputs`.
5. `runtime_minimal.launch.py` no longer shadows runtime profile audio settings with hardcoded values.
6. Added `scripts/run_benchmark_core.py` and rewired `run_benchmarks.sh`/`make bench` to the canonical profile-driven benchmark path.
7. Redirected `make report` to canonical `results/latest_benchmark_summary.json`.

## Practical Consequences

- `configs/deployment/dev_local.yaml` is no longer just documentation for benchmark/runtime defaults.
- provider profiles became a real extension mechanism instead of a hardcoded registry wrapper with decorative metadata.
- runtime profiles once again have end-to-end influence over the minimal runtime launch path.
- the default benchmark operator path now consumes canonical benchmark/provider/dataset profiles instead of `configs/default.yaml`.

## Deferred Work

1. Bind `configs/gui/default_gui.yaml` into gateway startup behavior.
2. Collapse or quarantine the old `configs/default.yaml` path behind an explicit compatibility boundary.
3. Decide whether the old direct `asr_benchmark.runner` should remain executable or move under an explicit compatibility namespace.
