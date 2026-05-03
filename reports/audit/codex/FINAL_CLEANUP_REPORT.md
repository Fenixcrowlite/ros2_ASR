# Final Cleanup Report

## Outcome

The default workspace is now canonical-only. `ros2_ws/src` contains 19 production packages:

- `asr_benchmark_core`
- `asr_benchmark_nodes`
- `asr_config`
- `asr_core`
- `asr_datasets`
- `asr_gateway`
- `asr_interfaces`
- `asr_launch`
- `asr_metrics`
- `asr_provider_aws`
- `asr_provider_azure`
- `asr_provider_base`
- `asr_provider_google`
- `asr_provider_huggingface`
- `asr_provider_vosk`
- `asr_provider_whisper`
- `asr_reporting`
- `asr_runtime_nodes`
- `asr_storage`

`colcon list --base-paths ros2_ws/src` shows only those packages. No `asr_backend_*`, `asr_ros`, or `asr_benchmark` packages remain in the default build graph.

## Archived To `legacy/`

- `legacy/ros2_packages/backends/`
  - `asr_backend_aws`
  - `asr_backend_azure`
  - `asr_backend_google`
  - `asr_backend_mock`
  - `asr_backend_vosk`
  - `asr_backend_whisper`
- `legacy/ros2_packages/asr_ros/`
- `legacy/ros2_packages/asr_benchmark/`
- `legacy/configs/flat/`
  - `default.yaml`
  - `live_mic_whisper.yaml`
  - all `web_latest_*.yaml`
  - all `web_ros_wrapper*.yaml`
  - `commercial.example.yaml`
- `legacy/scripts/`
  - `live_sample_eval.py`
  - `run_live_sample_eval.sh`
- `legacy/tests/`
  - legacy/backend-direct unit tests
  - legacy ROS recognize-once integration test
- `legacy/docs/`
  - old wiki
  - legacy-heavy architecture reports and UML
- `legacy/python/asr_core_factory.py`

## Canonical Refactor Completed

- Provider packages now own their implementation modules directly.
  - `asr_provider_aws.backend`
  - `asr_provider_azure.backend`
  - `asr_provider_google.backend`
  - `asr_provider_vosk.backend`
  - `asr_provider_whisper.backend`
- Provider adapters and gateway secret handling no longer import `asr_backend_*`.
- Provider package manifests no longer depend on `asr_backend_*`.
- `asr_gateway`, `asr_runtime_nodes`, and `asr_benchmark_core` now declare Hugging Face provider support where needed.
- Legacy factory registration was removed from canonical provider code.
- `asr_core.__init__` no longer exports `AsrBackend` or `create_backend`.
- `asr_metrics.__init__` no longer exports `MetricsCollector`.
- `asr_core.config` no longer auto-loads `configs/commercial.yaml`; the dead `load_runtime_config()` path was removed.

## Tooling And Docs Cleanup

- `Makefile` no longer exposes `build-legacy`, `test-unit-legacy`, or `live-sample`.
- `scripts/source_runtime_env.sh` no longer has legacy PYTHONPATH opt-in.
- `scripts/run_demo.sh` and `scripts/run_benchmarks.sh` no longer use `--packages-skip asr_ros asr_benchmark`.
- Canonical README/docs were rewritten around the provider/runtime/gateway architecture.
- `docs/arch/*` was regenerated from the canonical source graph.
  - `static_graph.json`, `merged_graph.json`, Mermaid outputs, and changelog no longer reference `asr_ros` or `asr_benchmark`.
  - `runtime_graph.json` is currently a placeholder because a live managed stack from this workspace was already running during capture.

## Validation

Executed successfully:

- `make build`
- `make test-unit`
- `make test-ros`
- `make test-colcon`
- `make bench`
- `make report`

Observed benchmark/report outputs:

- canonical run artifacts under `artifacts/benchmark_runs/bench_20260413T130728Z_83fc1eca/`
- compatibility exports still produced:
  - `results/benchmark_results.json`
  - `results/benchmark_results.csv`
- latest canonical report pointers updated:
  - `results/latest_benchmark_summary.json`
  - `results/latest_benchmark_run.json`
  - `results/report.md`

Static cleanup checks in the canonical tree are clean for:

- `from asr_backend_`
- `import asr_backend_`
- `create_backend(`
- `configs/default.yaml`
- `configs/live_mic_whisper.yaml`
- `/asr/set_backend`
- `build-legacy`
- `test-unit-legacy`
- `ASR_INCLUDE_LEGACY_PYTHONPATH`

## Intentionally Kept Compatibility

- `RecognizeOnce` remains the canonical one-shot ROS service.
- `ListBackends` remains compatibility-named in IDL, but now represents provider catalog semantics.
- Compatibility benchmark exports in `results/benchmark_results.*` are still generated for downstream report/plot consumers.
- `configs/commercial.yaml` remains an optional local file, but it is no longer auto-loaded by canonical runtime helpers.
- Historical audit documents remain at the repo root as records; they are not part of the canonical runtime/build path.

## Follow-Up Recommendations

- Stop the currently running managed ASR stack and rerun `make arch` to replace the placeholder runtime snapshot in `docs/arch/runtime_graph.json`.
- If desired, move root-level historical audit markdown/CSV files into `legacy/docs/` as a separate archival pass.
- Review benchmark artifact churn under `reports/benchmarks/` if you want this cleanup commit to exclude refreshed result snapshots.
