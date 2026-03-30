# Audit Phase 2: Dataflow

## Canonical runtime flow

1. Operator/UI selects runtime profile and provider profile.
2. Gateway calls ROS2 services on `asr_orchestrator_node`.
3. `asr_runtime_nodes.audio_input_node` produces audio chunks.
4. `audio_preprocess_node` normalizes sample rate/channels.
5. `vad_segmenter_node` creates segments for `segmented` mode.
6. `asr_orchestrator_node` resolves provider profile through `ProviderManager`.
7. Provider adapter returns `NormalizedAsrResult`.
8. Result is converted to ROS messages and surfaced through gateway/UI.

## Canonical benchmark flow

1. Operator/API submits benchmark request with benchmark profile + optional dataset/provider overrides.
2. `BenchmarkOrchestrator` resolves benchmark, dataset, metric, and provider profiles.
3. `BatchExecutor` or streaming executor runs provider x sample matrix.
4. Each sample produces normalized result row with quality support + metric payload.
5. `asr_metrics.summary.summarize_result_rows` builds run summary.
6. `ArtifactStore` persists:
   - manifest
   - `metrics/results.json`
   - `metrics/results.csv`
   - `reports/summary.json`
   - `reports/summary.md`

## Repaired local operator flow

1. `make bench` calls `scripts/run_benchmark_core.py`.
2. Script runs canonical `BenchmarkOrchestrator`.
3. Script exports compatibility artifacts for local operator workflows:
   - `results/latest_benchmark_summary.json`
   - `results/latest_benchmark_run.json`
   - `results/benchmark_results.json`
   - `results/benchmark_results.csv`
   - `results/plots/*`
4. `make report` renders from canonical summary input, not from the old runner path.

## Logs/diagnostics flow

1. UI logs page requests `/api/diagnostics/*` and `/api/logs`.
2. Gateway scans:
   - `logs/runtime`
   - `logs/benchmark`
   - `logs/gateway`
   - `logs/gui`
   - explicit `ROS_LOG_DIR` runtime fallback
3. Gateway now returns structured entries:
   - component
   - source/file
   - severity
   - timestamp when parseable
   - line number
   - message
4. Frontend renders structured log cards instead of opaque text dump.

## Structural breaks found

- Legacy benchmark path still exists and uses old backend-centric config surface.
- Legacy runtime ROS nodes still exist beside canonical runtime nodes.
- `live_sample_eval.py` still uses older backend/config semantics rather than the profile-driven provider core.
- Documentation drift makes some legacy paths look first-class even when they are not.
