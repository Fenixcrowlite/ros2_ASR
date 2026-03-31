# Repository Inventory

Audit date: `2026-03-31`

Verification basis for this inventory:

- repository scan of `ros2_ws/src`, `tests`, `scripts`, `docs`, `.github/workflows`, `web_ui`
- post-patch canonical workflow verification with `make build`, `make test-unit`, `make test-ros`, `make test-colcon`
- direct code inspection of the runtime, gateway, benchmark, config, metrics, dataset, and storage packages

## ROS2 Package Inventory

### Canonical Packages

| Package | Role | Status | Main files | Inputs | Outputs | Current risks |
|---|---|---|---|---|---|---|
| `asr_interfaces` | Canonical ROS contract surface | `CANONICAL` | `ros2_ws/src/asr_interfaces/msg/*`, `srv/*`, `action/*` | ROS clients, nodes, gateway | Generated message/service/action types | Legacy `asr_ros` still exposes overlapping older contracts. |
| `asr_config` | Profile resolution and config validation | `CANONICAL` | `ros2_ws/src/asr_config/asr_config/loader.py`, `secrets.py` | `configs/*`, env overrides, ROS overrides | Resolved config snapshots under `configs/resolved/`, validation errors | Runtime sessions do not yet persist a full session manifest like benchmark runs do. |
| `asr_storage` | Canonical artifact layout and persistence | `CANONICAL` | `ros2_ws/src/asr_storage/asr_storage/artifacts.py` | Runtime/benchmark payloads | `artifacts/runtime_sessions/*`, `artifacts/benchmark_runs/*` | Runtime session artifact coverage is weaker than benchmark artifact coverage. |
| `asr_metrics` | Benchmark metrics, summaries, observability namespace | `CANONICAL` | `ros2_ws/src/asr_metrics/asr_metrics/quality.py`, `summary.py`, `definitions.py`, `ros2_ws/src/asr_metrics/asr_observability/*` | Result rows, runtime traces, metric profiles | WER/CER summaries, trace exports, system samples | Runtime validator incorrectly caps `wer`/`cer` to `<= 1.0`; live runtime instrumentation is partial. |
| `asr_datasets` | Dataset registry, JSONL manifest loader, import helpers | `CANONICAL` | `ros2_ws/src/asr_datasets/asr_datasets/manifest.py`, `registry.py` | Dataset profiles, JSONL manifests, import folders | `DatasetSample` lists, registry records | Canonical manifest loader is deterministic now; legacy benchmark loader still has `cwd` fallback. |
| `asr_provider_whisper` | Whisper provider adapter | `CANONICAL` | `ros2_ws/src/asr_provider_whisper/asr_provider_whisper/whisper_provider.py` | Provider profile, `ProviderAudio` | `NormalizedAsrResult` | Model load time and warm/cold behavior are not exposed as first-class metrics. |
| `asr_provider_vosk` | Vosk provider adapter | `CANONICAL` | `ros2_ws/src/asr_provider_vosk/asr_provider_vosk/vosk_provider.py` | Provider profile, `ProviderAudio` | `NormalizedAsrResult` | Same missing model lifecycle metrics; confidence semantics vary by provider. |
| `asr_provider_google` | Google provider adapter | `CANONICAL` | `ros2_ws/src/asr_provider_google/asr_provider_google/google_provider.py` | Provider profile, credentials ref, `ProviderAudio` | `NormalizedAsrResult` | Gateway status can overstate readiness by counting profiles instead of validated runtime auth. |
| `asr_provider_aws` | AWS provider adapter | `CANONICAL` | `ros2_ws/src/asr_provider_aws/asr_provider_aws/aws_provider.py` | Provider profile, credentials ref, `ProviderAudio` | `NormalizedAsrResult` | Same readiness/status honesty gap; cost metadata is estimated rather than measured. |
| `asr_provider_azure` | Azure provider adapter | `CANONICAL` | `ros2_ws/src/asr_provider_azure/asr_provider_azure/azure_provider.py` | Provider profile, credentials ref, `ProviderAudio` | `NormalizedAsrResult` | Same readiness/status honesty gap; confidence semantics are provider-specific. |
| `asr_runtime_nodes` | Canonical runtime pipeline | `CANONICAL` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py`, `audio_preprocess_node.py`, `vad_segmenter_node.py`, `asr_orchestrator_node.py` | Runtime/profile services, audio file or mic, ROS topics | Runtime services, topics, direct recognition, session control | Live segmented/provider-stream runtime does not yet export per-segment traces; `audio_preprocess_node` and `vad_segmenter_node` still use `list(...)` for audio payloads. |
| `asr_benchmark_core` | Canonical benchmark planner/executor | `CANONICAL` | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py`, `executor.py`, `noise.py` | Benchmark profile, dataset profile, provider profiles, metrics profiles | Run manifests, results JSON/CSV, summaries, trace exports | Corrupted-trace handling exists per sample but aggregate summaries do not yet quarantine corrupted runs. |
| `asr_benchmark_nodes` | ROS-facing benchmark shell | `CANONICAL` | `ros2_ws/src/asr_benchmark_nodes/asr_benchmark_nodes/benchmark_manager_node.py` | ROS actions/services | `/benchmark/run_experiment`, `/datasets/import`, status services | Action duration is not exported as a first-class metric. |
| `asr_gateway` | GUI/API to ROS bridge | `CANONICAL` | `ros2_ws/src/asr_gateway/asr_gateway/api.py`, `ros_client.py`, `main.py` | HTTP requests, config/secrets, ROS services/actions/topics | FastAPI endpoints, runtime snapshots, benchmark control | `GatewayRosClient` still creates short-lived nodes/executors per request; provider catalog status is optimistic. |
| `asr_launch` | Canonical launch entrypoints | `CANONICAL` | `ros2_ws/src/asr_launch/launch/*.launch.py`, `ros2_ws/src/asr_launch/README.md` | ROS parameters, profiles | Canonical launch stacks | Some docs outside `README.md` still describe legacy entrypoints without a strong deprecation banner. |

### Internal Support Packages

| Package | Role | Status | Main files | Inputs | Outputs | Current risks |
|---|---|---|---|---|---|---|
| `asr_core` | Shared models, audio utilities, namespaces, shutdown helpers | `INTERNAL SUPPORT` | `ros2_ws/src/asr_core/asr_core/audio.py`, `models.py`, `namespaces.py` | Provider/runtime/benchmark callers | Shared helpers and contracts | Utility layer is broad; needs continued discipline to avoid becoming a dumping ground. |
| `asr_provider_base` | Provider manager and provider contract | `INTERNAL SUPPORT` | `ros2_ws/src/asr_provider_base/asr_provider_base/provider_manager.py`, `catalog.py` | Provider profiles, config root | Provider instances, capability discovery | Correctness depends on honest capability reporting from adapters. |
| `asr_reporting` | Report shaping helpers | `INTERNAL SUPPORT` | `ros2_ws/src/asr_reporting/*` | Benchmark summaries | Export/report formatting | Depends on upstream metrics completeness; does not validate semantics itself. |
| `asr_backend_mock` | Mock backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_mock/*` | Test/runtime inputs | Backend responses | Direct use would bypass canonical provider layer. |
| `asr_backend_whisper` | Whisper backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_whisper/*` | Provider adapter calls | Backend responses | Duplicate abstraction layer relative to provider adapters remains a maintenance burden. |
| `asr_backend_vosk` | Vosk backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_vosk/*` | Provider adapter calls | Backend responses | Same duplication risk. |
| `asr_backend_google` | Google backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_google/*` | Provider adapter calls | Backend responses | Same duplication risk. |
| `asr_backend_aws` | AWS backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_aws/*` | Provider adapter calls | Backend responses | Same duplication risk. |
| `asr_backend_azure` | Azure backend implementation detail | `INTERNAL SUPPORT` | `ros2_ws/src/asr_backend_azure/*` | Provider adapter calls | Backend responses | Same duplication risk. |

### Legacy Packages

| Package | Role | Status | Main files | Inputs | Outputs | Current risks |
|---|---|---|---|---|---|---|
| `asr_ros` | Legacy runtime/action/service stack | `LEGACY` | `ros2_ws/src/asr_ros/asr_ros/asr_server_node.py`, `audio_capture_node.py`, `asr_text_output_node.py`, `launch/*.launch.py` | Old ROS services/actions/topics | `/asr/recognize_once`, `/asr/transcribe`, `/asr/text`, `/asr/audio_chunks` | Overlaps canonical runtime truth; retained only for compatibility. Default build/test flow now skips it. |
| `asr_benchmark` | Legacy benchmark runner | `LEGACY` | `ros2_ws/src/asr_benchmark/asr_benchmark/runner.py`, `dataset.py`, `benchmark_node.py` | Old CSV manifests, legacy config | Legacy benchmark JSON/CSV and node | `dataset.py` still resolves audio via `Path.cwd()`, making runs non-deterministic if manually used. Default build/test flow now skips it. |

## Runtime, Benchmark, and Gateway Entrypoints

| Entrypoint | Surface | Contract |
|---|---|---|
| `audio_input_node` | `asr_runtime_nodes` console script | Publishes `AudioChunk` on `/asr/runtime/audio/raw`; serves `/asr/runtime/audio/start_session`, `/stop_session`, `/reconfigure`. |
| `audio_preprocess_node` | `asr_runtime_nodes` console script | Consumes raw chunks, republishes `/asr/runtime/audio/preprocessed`, serves `/asr/runtime/preprocess/reconfigure`. |
| `vad_segmenter_node` | `asr_runtime_nodes` console script | Consumes preprocessed chunks, publishes `SpeechActivity` and `AudioSegment`, serves `/asr/runtime/vad/reconfigure`. |
| `asr_orchestrator_node` | `asr_runtime_nodes` console script | Hosts `/asr/runtime/start_session`, `/stop_session`, `/reconfigure`, `/recognize_once`, `/get_status`, `/list_backends`, `/config/list_profiles`, `/config/validate`; publishes final/partial results and status topics. |
| `benchmark_manager_node` | `asr_benchmark_nodes` console script | Hosts `/benchmark/run_experiment`, `/datasets/import`, `/benchmark/get_status`, `/datasets/register`, `/datasets/list`. |
| `asr_gateway_server` | `asr_gateway` console script | Serves FastAPI/uvicorn gateway, frontend, benchmark/runtime APIs. |
| `scripts/run_benchmark_core.py` | Canonical CLI benchmark entry | Calls `BenchmarkOrchestrator.run()` directly without ROS. |
| `scripts/run_demo.sh` | Canonical developer runtime entry | Builds canonical packages only, launches `asr_launch/runtime_minimal.launch.py`. |
| `scripts/run_benchmarks.sh` | Canonical developer benchmark entry | Builds canonical packages only, runs `scripts/run_benchmark_core.py`. |
| `scripts/run_web_ui.sh` | Canonical GUI entry | Starts `asr_launch/full_stack_dev.launch.py` or `gateway_with_runtime.launch.py`. |

## ROS Interface Inventory

- Messages:
  - `AudioChunk.msg`, `AudioSegment.msg`, `SpeechActivity.msg`
  - `AsrResult.msg`, `AsrResultPartial.msg`, `AsrMetrics.msg`
  - `NodeStatus.msg`, `SessionStatus.msg`, `BenchmarkJobStatus.msg`, `DatasetStatus.msg`, `ExperimentSummary.msg`
  - `MetricArtifactRef.msg`, `ResultArtifactRef.msg`, `AsrEvent.msg`, `WordTimestamp.msg`
- Services:
  - Runtime: `RecognizeOnce.srv`, `StartRuntimeSession.srv`, `StopRuntimeSession.srv`, `ReconfigureRuntime.srv`, `GetAsrStatus.srv`, `ListBackends.srv`
  - Config: `ListProfiles.srv`, `ValidateConfig.srv`
  - Benchmark/data: `GetBenchmarkStatus.srv`, `RegisterDataset.srv`, `ListDatasets.srv`
  - Legacy compatibility: `SetAsrBackend.srv`
- Actions:
  - Runtime/legacy: `Transcribe.action`, `StreamSession.action`
  - Benchmark/data: `RunBenchmarkExperiment.action`, `ImportDataset.action`, `GenerateReport.action`, `DownloadModel.action`

## Launch Files

| Launch file | Status | Purpose | Risk |
|---|---|---|---|
| `ros2_ws/src/asr_launch/launch/runtime_minimal.launch.py` | `CANONICAL` | Minimal runtime service stack | Canonical path, verified via `scripts/run_demo.sh`. |
| `ros2_ws/src/asr_launch/launch/runtime_streaming.launch.py` | `CANONICAL` | Streaming runtime stack | Live segmented/provider-stream trace export is still partial. |
| `ros2_ws/src/asr_launch/launch/gateway_with_runtime.launch.py` | `CANONICAL` | Runtime + gateway | Gateway per-request node churn still present. |
| `ros2_ws/src/asr_launch/launch/full_stack_dev.launch.py` | `CANONICAL` | Runtime + benchmark + gateway + UI | Multi-component stack is correct baseline but still carries gateway inefficiency. |
| `ros2_ws/src/asr_launch/launch/benchmark_single_provider.launch.py` | `CANONICAL` | Single-provider benchmark stack | Action latency not exported. |
| `ros2_ws/src/asr_launch/launch/benchmark_matrix.launch.py` | `CANONICAL` | Matrix benchmark stack | No first-class matrix export artifact yet in `reports/benchmarks/`. |
| `ros2_ws/src/asr_ros/launch/bringup.launch.py` | `LEGACY` | Old runtime bringup | Should not be part of normal workflow. |
| `ros2_ws/src/asr_ros/launch/demo.launch.py` | `LEGACY` | Old demo launch | Same overlap risk. |
| `ros2_ws/src/asr_ros/launch/benchmark.launch.py` | `LEGACY` | Old benchmark launch | Same overlap risk. |

## Gateway / Web UI Surface

- Backend entrypoint: `ros2_ws/src/asr_gateway/asr_gateway/main.py`
- Main API implementation: `ros2_ws/src/asr_gateway/asr_gateway/api.py`
- ROS bridge helper: `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py`
- Frontend shell: `web_ui/frontend/index.html`
- Frontend runtime page: `web_ui/frontend/js/pages/runtime.js`
- Frontend benchmark page: `web_ui/frontend/js/pages/benchmark.js`

Current gateway risks:

- request-scoped ROS nodes/executors in `GatewayRosClient._node()`, `_call_service()`, `_call_action()`
- provider catalog status uses profile count, not validated readiness
- runtime live view depends on observer state plus API normalization rather than a single canonical session artifact

## Config, Secrets, Datasets, Storage, and Observability Stack

- Config resolution:
  - `ros2_ws/src/asr_config/asr_config/loader.py::resolve_profile`
  - merge order is explicit and snapshotting is built-in
- Secret handling:
  - secret references in `secrets/refs/*.yaml`
  - local runtime injection file `secrets/local/runtime.env`
  - resolver/masking in `ros2_ws/src/asr_config/asr_config/secrets.py`
- Dataset handling:
  - canonical manifest loader `ros2_ws/src/asr_datasets/asr_datasets/manifest.py`
  - registry `ros2_ws/src/asr_datasets/asr_datasets/registry.py`
  - import helpers in `scripts/import_dataset/*`
- Observability:
  - trace collector `ros2_ws/src/asr_metrics/asr_observability/collectors/pipeline.py`
  - analyzers `ros2_ws/src/asr_metrics/asr_observability/analyzers/runtime.py`
  - validators `ros2_ws/src/asr_metrics/asr_observability/validators/runtime.py`
  - exporters `ros2_ws/src/asr_metrics/asr_observability/exporters/files.py`
- Artifact persistence:
  - runtime sessions under `artifacts/runtime_sessions/<session_id>/...`
  - benchmark runs under `artifacts/benchmark_runs/<run_id>/...`
  - compatibility summary copies under `reports/benchmarks/<run_id>/...`

## Tests, CI, Packaging, and Documentation

- Test directories:
  - `tests/unit`, `tests/component`, `tests/contract`, `tests/api`, `tests/integration`, `tests/gui`, `tests/e2e`, `tests/regression`
- Default marker policy:
  - canonical default excludes `legacy` and non-selected `ros`
  - explicit `legacy` markers now identify legacy runtime/benchmark tests
- CI:
  - `.github/workflows/ci.yml`
  - current jobs: `ruff`, `mypy`, `unit-tests`, `ros-jazzy-colcon`
- Packaging/release:
  - root `pyproject.toml`, `requirements.txt`, `Makefile`
  - per-package `package.xml` and `setup.py`
  - release scripts: `scripts/make_dist.sh`, `scripts/release_check.sh`, `scripts/secret_scan.sh`
- Canonical usage docs:
  - `README.md`
  - `docs/run_guide.md`
  - `docs/architecture/system_overview.md`
  - `docs/architecture/runtime_architecture.md`
  - `docs/architecture/benchmark_architecture.md`
  - `ros2_ws/src/asr_launch/README.md`
- Legacy/deprecation docs:
  - `ros2_ws/src/asr_ros/README.md`
  - `docs/architecture/migration_plan.md`

Primary documentation risks:

- wiki pages under `docs/wiki/02_ROS2/*` and older interface docs still need a canonical/legacy banner review
- root `requirements.txt` is still a monolith mixing runtime, cloud, web, and dev dependencies
