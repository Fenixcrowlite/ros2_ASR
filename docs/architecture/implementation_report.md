# Implementation Report: Modular ROS2-First ASR Platform Baseline

## 1. What was found in the old project

The repository already had a functional baseline:
- ROS2 runtime package (`asr_ros`) with one-node-centric orchestration.
- Provider packages (`asr_backend_*`) with substantial working integrations.
- Benchmark package (`asr_benchmark`) and metrics package (`asr_metrics`).
- Web backend (`web_gui`) with practical controls but mixed architectural responsibilities.

Main issues were architectural coupling (runtime/benchmark/web), flat config model, and missing first-class artifact/secrets/profile boundaries.

## 2. What was preserved and reused

Reused directly:
- Core audio/language helpers from `asr_core`.
- Existing provider runtime logic from `asr_backend_whisper`, `asr_backend_vosk`, `asr_backend_azure`, `asr_backend_google`, `asr_backend_aws`.
- WER/CER implementations from `asr_metrics.quality`.

Reused with adaptation:
- Legacy provider code is now wrapped by adapter implementations in `asr_provider_*`.
- Existing benchmark behavior informed new `asr_benchmark_core` executor/orchestrator flow.

## 3. What was rewritten/restructured

Rewritten or added as new architecture layers:
- Expanded `asr_interfaces` with runtime/benchmark/session/artifact contracts.
- New provider abstraction package: `asr_provider_base`.
- New runtime pipeline package: `asr_runtime_nodes`.
- New profile/secret resolver package: `asr_config`.
- New storage/artifact layer: `asr_storage`.
- New dataset subsystem: `asr_datasets`.
- New benchmark core and ROS wrapper: `asr_benchmark_core`, `asr_benchmark_nodes`.
- New gateway API package: `asr_gateway`.
- New launch package: `asr_launch`.
- New web baseline skeleton: `web_ui/frontend`, `web_ui/backend`.

## 4. New packages created

Created in `ros2_ws/src`:
- `asr_runtime_nodes`
- `asr_provider_base`
- `asr_provider_whisper`
- `asr_provider_vosk`
- `asr_provider_azure`
- `asr_provider_google`
- `asr_provider_aws`
- `asr_config`
- `asr_storage`
- `asr_datasets`
- `asr_benchmark_core`
- `asr_benchmark_nodes`
- `asr_reporting`
- `asr_gateway`
- `asr_launch`

Also expanded existing target packages:
- `asr_interfaces`
- `asr_core`
- `asr_metrics`

## 5. Config model implemented

Implemented profile-driven configuration with deterministic precedence in `asr_config.loader`.

Profile directories:
- `configs/runtime`
- `configs/providers`
- `configs/benchmark`
- `configs/datasets`
- `configs/metrics`
- `configs/deployment`
- `configs/gui`
- `configs/resolved`

Secret model:
- refs in `secrets/refs/*.yaml`
- resolved via env/file injection
- masked handling utility
- provider configs keep only `credentials_ref`

## 6. Provider integrations status

Working baseline adapters:
- `whisper` local adapter (`asr_provider_whisper`) using legacy backend wrapper.
- `google` cloud adapter (`asr_provider_google`) with native gRPC streaming path + secret/file injection.
- `azure` cloud adapter (`asr_provider_azure`) with native push-stream continuous recognition + env-based secret injection.
- `aws` cloud adapter (`asr_provider_aws`) with native `StartStreamTranscription` path + env/profile-based auth.
- `vosk` local adapter (`asr_provider_vosk`) with native local streaming.

Resilience note:
- `WhisperProvider` no longer substitutes synthetic transcripts. When decode fails or returns an empty transcript for non-silent audio, the normalized result is marked degraded/error and exposed honestly to runtime, benchmark, and GUI layers.
- Runtime and benchmark sample assets were replaced with real spoken WAV fixtures (`en_zero.wav`, `en_one.wav`) so the baseline can be demonstrated without synthetic transcript substitution.

Note: real cloud execution depends on local credential/environment setup.

## 7. Runtime pipeline status

Implemented runtime roles in `asr_runtime_nodes`:
- `audio_input_node`
- `audio_preprocess_node`
- `vad_segmenter_node`
- `asr_orchestrator_node`

Implemented runtime communication baseline:
- audio/topics flow (`raw -> preprocessed -> segments`)
- partial/final normalized result topics
- node/session status topics
- runtime services (`start/stop/reconfigure/recognize_once/list_backends/list_profiles/validate/get_status`)

Smoke-verified:
- runtime minimal launch starts all nodes.
- recognize-once service path returns normalized response structure end-to-end.
- file runtime path now carries truthful source metadata across `audio_input -> preprocess -> VAD -> orchestrator`, producing real Whisper output instead of hidden fallback behavior.
- microphone runtime path was rechecked after the same pipeline fixes and now produces real final transcripts through the same nodes.

## 8. Benchmark pipeline status

Implemented:
- dataset manifest model and loader (`jsonl`)
- dataset registry and folder import
- benchmark orchestrator + batch executor
- plugin metric engine baseline (WER/CER/latency/success/failure)
- reproducible run persistence in per-run folder
- benchmark ROS node with action/service API

Smoke-verified:
- benchmark manager action executes end-to-end and emits summary/result artifacts.
- benchmark sample runs against `sample_dataset` now execute on real spoken fixtures and persist honest Whisper outputs in `normalized_outputs/`.
- benchmark text metrics now normalize punctuation/case at the metric layer, so baseline WER/CER reflect speech quality rather than formatting artifacts like `Hello.` vs `hello`.

## 9. Storage/artifact model status

Implemented `asr_storage.ArtifactStore`:
- runtime session directory creation
- benchmark run directory creation with fixed substructure
- manifest/raw/normalized/metric/report persistence
- artifact metadata references (path/checksum/size)

Verified by executed benchmark run artifacts in `artifacts/benchmark_runs/<run_id>/...`.

## 10. Gateway/GUI model status

Implemented `asr_gateway`:
- FastAPI API
- ROS service/action bridge
- endpoints for runtime, benchmark, datasets, config validation, artifacts, secret refs

Implemented `web_ui` skeleton with required page set:
- dashboard
- runtime control
- providers
- profiles
- datasets
- benchmark
- results
- logs/diagnostics
- secrets/credentials metadata

Legacy `web_gui` is retained as compatibility layer and considered deprecated as architecture control plane.

## 11. Design decisions

1. Keep legacy packages buildable during migration.
Reason: avoid hard break and preserve operational baseline.

2. Wrap legacy provider logic in new adapters rather than rewrite SDK code immediately.
Reason: lower migration risk while enforcing clean provider contract.

3. Introduce profile/secrets/storage as independent packages.
Reason: remove ad-hoc YAML reads and centralize reproducibility/security rules.

4. Build runtime as multi-node pipeline (input/preprocess/vad/orchestrator), not one giant node.
Reason: align with ROS2-first composable/distributed architecture.

5. Keep benchmark subsystem separate from runtime pipeline.
Reason: clean boundary for reproducibility and experimental workflows.

6. Enforce gateway boundary for GUI interactions.
Reason: GUI should not become system-of-record for core logic.

## 12. Migration/deprecation status

Documented in:
- `docs/architecture/repo_assessment.md`
- `docs/architecture/migration_plan.md`

Deprecated-by-architecture (kept for compatibility):
- `asr_ros` as primary runtime package
- `asr_benchmark` as primary benchmark package
- direct `web_gui` control-plane logic
- flat config-only operation model

## 13. What works end-to-end now

Working baseline paths:
1. Runtime launch and recognition service flow through new runtime nodes.
2. Benchmark action execution through new benchmark nodes/core with artifact persistence.
3. Gateway launch and API startup with runtime bridge.
4. Profile resolution + resolved snapshot generation.
5. Runtime file session on `data/sample/vosk_test.wav` produces a real transcript from the built-in spoken-number sample via the full ROS2 pipeline.
6. Runtime microphone session produces live final Whisper output without file/mock fallback.
7. Benchmark run on `sample_dataset` + `providers/whisper_local` completes with real artifacts and normalized WER/CER.

## 14. What is scaffolding/extension hook

Scaffolding and hooks (not fully production-complete yet):
- advanced streaming action flow and report-generation action wiring,
- advanced robustness/noise scenarios,
- richer resource/cost metrics plugins,
- full composable deployment profiles,
- comprehensive UI integration beyond baseline skeleton.

## 15. Future work (post-baseline)

- Add lifecycle-managed runtime nodes and composable variants.
- Expand provider diagnostics and health monitoring.
- Add GPU/resource/cost metrics with provider-specific calculators.
- Add automated comparison reports across benchmark runs.
- Complete migration of legacy scripts/tests to new package topology.

## 16. Verification executed in this cycle

1. Full workspace build:
- `colcon build --base-paths ros2_ws/src --symlink-install`

2. Runtime launch smoke:
- `ros2 launch asr_launch runtime_minimal.launch.py`

3. Runtime recognize-once service smoke:
- `ros2 service call /asr/runtime/recognize_once asr_interfaces/srv/RecognizeOnce ...`

4. Benchmark action smoke:
- `ros2 action send_goal /benchmark/run_experiment asr_interfaces/action/RunBenchmarkExperiment ...`

5. Gateway API smoke:
- `ros2 launch asr_launch gateway_with_runtime.launch.py`
- `curl http://127.0.0.1:8088/api/health`
- `POST /api/runtime/recognize_once`
- `POST /api/benchmark/run`

6. Honest runtime verification after fallback removal:
- `POST /api/runtime/start` with `audio_source=file`, `audio_file_path=data/sample/vosk_test.wav`
- verified `recent_results[0].text` is populated from the built-in spoken-number sample without mock/fallback markers
- `POST /api/runtime/start` with `audio_source=mic`
- verified live runtime final output appears without mock/fallback markers

7. Honest benchmark verification after metric normalization:
- `POST /api/benchmark/run` with a dedicated truth-aligned sample run id
- verified the built-in sample dataset completes with persisted metrics and non-empty normalized outputs
