# Audit Phase 2 Dataflow

## Canonical Runtime Dataflow

### Segmented runtime path

1. Operator/UI starts runtime through gateway:
   - HTTP `POST /api/runtime/start`
   - gateway preflight resolves runtime and provider profiles
   - gateway calls ROS service `/asr/runtime/start_session`
2. `asr_orchestrator_node` resolves:
   - runtime profile via `asr_config.resolve_profile`
   - provider profile via `ProviderManager`
   - provider preset/settings overrides via `resolve_provider_execution`
3. Runtime stage reconfiguration fans out to:
   - `/asr/runtime/audio/reconfigure`
   - `/asr/runtime/preprocess/reconfigure`
   - `/asr/runtime/vad/reconfigure`
4. Audio path:
   - `audio_input_node` publishes `/asr/runtime/audio/raw`
   - `audio_preprocess_node` publishes `/asr/runtime/audio/preprocessed`
   - `vad_segmenter_node` publishes `/asr/runtime/audio/segments`
5. `asr_orchestrator_node` consumes segments and calls the resolved provider adapter.
6. Provider adapter delegates to backend substrate / SDK and returns `NormalizedAsrResult`.
7. Orchestrator publishes:
   - `/asr/runtime/results/final`
   - `/asr/runtime/results/partial`
   - `/asr/status/nodes`
   - `/asr/status/sessions`
8. `asr_gateway.ros_client.RuntimeObserver` caches topic activity for the browser UI.

### Provider-stream runtime path

1. Same start flow as above.
2. Difference:
   - orchestrator requires `processing_mode=provider_stream`
   - provider adapter must advertise streaming support
   - orchestrator consumes `/asr/runtime/audio/preprocessed` chunks directly
3. Streaming-capable providers:
   - `vosk`
   - `google`
   - `aws`
   - `azure`

## Canonical Direct One-Shot Recognition Path

1. HTTP `POST /api/runtime/recognize_once`
2. Gateway resolves provider/runtime intent and calls ROS service `/asr/runtime/recognize_once`
3. Orchestrator optionally resolves a temporary provider from profile + preset + settings override
4. Provider adapter runs `recognize_once`
5. Gateway returns normalized result payload and also records recent result in runtime observer cache

## Canonical Benchmark Dataflow

### Direct benchmark-core path

1. `BenchmarkOrchestrator.run(BenchmarkRunRequest)` is called directly
2. Orchestrator resolves:
   - benchmark profile
   - dataset profile
   - metric profiles
   - provider profiles
3. Orchestrator writes run manifest and resolved-config references under `artifacts/benchmark_runs/<run_id>/`
4. `BatchExecutor` runs each `(provider, sample, noise variant)` combination
5. `MetricEngine` evaluates enabled metrics per sample
6. `summarize_result_rows` computes aggregate and per-provider summaries
7. `ArtifactStore` persists:
   - run manifest
   - raw outputs
   - normalized outputs
   - metrics/results.json
   - metrics/results.csv
   - reports/summary.json
   - reports/summary.md

### Gateway / ROS benchmark path

1. HTTP `POST /api/benchmark/run`
2. Gateway preflight validates benchmark profile, dataset manifest, and quality-reference availability
3. Gateway submits ROS action `/benchmark/run_experiment`
4. `benchmark_manager_node` builds `BenchmarkOrchestrator`
5. Orchestrator executes same core benchmark path as above
6. Gateway polls action/service status and reads generated artifacts for UI pages

### Operator benchmark CLI path

1. `bash scripts/run_benchmarks.sh`
2. Script sources runtime environment and builds the workspace
3. Script invokes `python3 scripts/run_benchmark_core.py`
4. `run_benchmark_core.py` calls `BenchmarkOrchestrator.run(...)`
5. Canonical artifacts land under `artifacts/benchmark_runs/<run_id>/...`
6. Compatibility export is derived from the canonical run into:
   - `results/latest_benchmark_summary.json`
   - `results/latest_benchmark_run.json`
   - `results/benchmark_results.json`
   - `results/benchmark_results.csv`
   - `results/plots/*`

## Config Resolution Dataflow

1. `resolve_profile(profile_type, profile_id, configs_root, deployment_profile, ...)`
2. Merge order:
   - `_base.yaml`
   - deployment profile payload relevant to the target profile type
   - inherited profile tree
   - related profiles
   - launch overrides
   - env overrides
   - ROS parameter overrides
   - session overrides
3. Resolved payload snapshot written into `configs/resolved/`

## Broken / Fake / Ambiguous Dataflow Surfaces

- `configs/providers/*.yaml::adapter` existed but was ignored before repair
- `configs/benchmark/*.yaml::execution_mode` existed but was ignored by benchmark core before repair
- deployment-scoped benchmark defaults existed but were ignored before repair
- `runtime_minimal.launch.py` overrode runtime profile audio settings before repair
- `configs/gui/default_gui.yaml` is still not consumed by gateway bootstrap
- `results/benchmark_results.*` are still present, but they are now compatibility mirrors rather than the source-of-truth artifact surface

See also:

- `REAL_EXECUTION_PATHS.md`
- `BROKEN_OR_FAKE_PATHS.md`
