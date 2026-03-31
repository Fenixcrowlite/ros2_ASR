# Pipeline Map

Audit date: `2026-03-31`

This file traces the real execution paths that currently exist in code. The tables below use the current canonical stack unless explicitly marked otherwise.

Instrumentation status vocabulary:

- `good`: explicit high-resolution stage timing or exported artifact exists
- `partial`: some timing/data exists, but not as a complete persisted trace
- `missing`: no first-class instrumentation was found in the current path

## A. `RecognizeOnce` Service Flow

Entrypoint contract: ROS service `/asr/runtime/recognize_once`

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| Service entry | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py::_on_recognize_once` | `RecognizeOnce.Request` -> in-memory request context | synchronous | `partial` | low | Initializes `PipelineTraceCollector` but does not time request parsing as its own stage. |
| Audio loading point | `.../asr_orchestrator_node.py::_read_recognize_audio_bytes` | `wav_path` -> raw WAV bytes | synchronous | `good` | low on local disk, higher on slow storage | Wrapped in explicit `audio_load` stage. |
| Config / provider resolution | `.../asr_orchestrator_node.py::_build_overrides_from_request`, `_resolve_recognize_provider` | request overrides -> provider instance + resolved profile | synchronous | `missing` | low | Correct logical step, but no dedicated timing metric today. |
| Inference point | provider adapter `recognize_once()` from `ros2_ws/src/asr_provider_*/...` | `ProviderAudio` -> `NormalizedAsrResult` | synchronous | `good` | dominant | Wrapped in explicit `provider_recognize` stage. |
| Postprocessing point | provider adapter latency fields copied by orchestrator | provider result -> ROS message fields | synchronous | `partial` | low | Relies on provider-reported `preprocess_ms`, `inference_ms`, `postprocess_ms`; no orchestrator-side postprocess timer. |
| Metrics creation point | `ros2_ws/src/asr_metrics/asr_observability/analyzers/runtime.py::build_runtime_trace` | collector stages + provider latency fields -> runtime trace metrics | synchronous | `good` | low | Produces `audio_load_ms`, stage breakdown, `total_latency_ms`, `time_to_result_ms`, `real_time_factor`, optional system metrics. |
| Result publication / return | `.../asr_orchestrator_node.py::_copy_result_message`, `_publish_result` | normalized result -> service response + `/asr/runtime/results/final` | sync service + async topic publish | `partial` | low | Topic publish is not separately timed. |
| Artifact persistence point | `.../asr_orchestrator_node.py::_export_runtime_trace` -> `ros2_ws/src/asr_metrics/asr_observability/exporters/files.py` | runtime trace -> JSON/CSV under `artifacts/runtime_sessions/<session_id>/metrics/` | synchronous file write | `good` | low | Only happens when observability config is enabled. |

## B. GUI-Triggered Recognition Flow

Entrypoint contract: browser `POST /api/runtime/recognize_once`

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| GUI trigger | `web_ui/frontend/js/pages/runtime.js::recognizeOnce` | form state -> JSON payload | asynchronous browser event | `missing` | low | No persistent client-side trace artifact. |
| HTTP client call | `web_ui/frontend/js/api.js::runtimeRecognizeOnce` | browser payload -> HTTP request | asynchronous | `missing` | low | No canonical client timing export. |
| API preflight / config resolution | `ros2_ws/src/asr_gateway/asr_gateway/api.py::runtime_recognize_once` | HTTP payload -> validated provider/sample request | synchronous | `partial` | low | Validates selected provider profile and sample path before ROS call. |
| ROS bridge request creation | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py::recognize_once` | validated payload -> `RecognizeOnce.Request` | synchronous | `partial` | low | Records service wait/call timing in response payload, but not as an exported gateway trace artifact. |
| ROS service transport | `.../ros_client.py::_call_service` | request -> service response | synchronous with short-lived executor spin | `partial` | low to medium | Confirmed inefficiency: a short-lived ROS node/executor is created per request. |
| Runtime recognition core | canonical flow A above | service request -> result | synchronous | `good` | dominant | Gateway delegates to runtime orchestrator service. |
| HTTP response send | `ros2_ws/src/asr_gateway/asr_gateway/api.py::runtime_recognize_once` | service payload -> JSON response | synchronous | `partial` | low | No dedicated gateway request/response stage trace. |
| GUI-visible result refresh | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py::RuntimeObserver` + `/api/runtime/live` | ROS topic/state -> live runtime snapshot | async subscriber + polling/read | `partial` | medium for perceived UX | Observer is persistent, but recognize-once bridge client is not. |

## C. Runtime Session Flow

Entrypoint contract: `POST /api/runtime/start` or direct ROS service `/asr/runtime/start_session`

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| GUI/API trigger | `web_ui/frontend/js/pages/runtime.js`, `ros2_ws/src/asr_gateway/asr_gateway/api.py::runtime_start` | runtime form -> `StartRuntimeSession` request | async UI + synchronous API | `missing` | low | No persisted client trace. |
| ROS bridge start call | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py::start_runtime` | HTTP payload -> ROS service response | synchronous | `partial` | low | Same per-request node/executor pattern as recognize-once. |
| Config resolution | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py::_on_start_session` | runtime/provider profile IDs -> resolved runtime state | synchronous | `partial` | low | Uses `resolve_profile` and provider manager; no session manifest is persisted. |
| Downstream node reconfigure | `.../asr_orchestrator_node.py::_call_service` | runtime profile -> preprocess/VAD/audio node configuration | synchronous service fan-out | `partial` | low | Returns resolved config refs, but session-level snapshot collation is missing. |
| Audio source start | `.../asr_orchestrator_node.py::_start_audio_session`, `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py::_on_start_session` | session config -> active audio source worker | synchronous control + async worker | `partial` | low | Status messages exist; no dedicated trace stage. |
| Audio load / capture | `.../audio_input_node.py::_publish_chunk` and source worker | file or mic input -> `/asr/runtime/audio/raw` `AudioChunk` | asynchronous topic publish | `partial` | medium for paced file replay, variable for mic | Audio input status topic exists. Audio file pacing strongly affects time-to-first-result. |
| Preprocessing point | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py::_on_chunk` | raw `AudioChunk` -> normalized/resampled `AudioChunk` | asynchronous topic transform | `missing` | medium | No persisted stage timing; current implementation still converts bytes with `list(data)`. |
| VAD / segmentation point | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py::_on_chunk`, `_flush_segment` | preprocessed chunks -> `SpeechActivity` + `AudioSegment` | asynchronous topic transform | `partial` | medium to high | Publishes activity and logs flush events, but no exported latency metric or drop/backpressure metric exists. |
| Inference point (segmented) | `.../asr_orchestrator_node.py::_on_segment` | `AudioSegment` -> final `NormalizedAsrResult` | synchronous callback | `partial` | dominant per utterance | No `PipelineTraceCollector` is used here yet. |
| Inference point (provider stream mode) | `.../asr_orchestrator_node.py::_on_preprocessed_chunk`, `_forward_stream_audio`, `_finish_provider_stream` | preprocessed chunks -> partial/final provider results | asynchronous callbacks | `partial` | dominant | Partial counts and first-partial metrics exist only in benchmark streaming path, not live runtime. |
| Result publication | `.../asr_orchestrator_node.py::_publish_partial_result`, `_publish_result` | provider result -> result topics | asynchronous topic publish | `partial` | low | Message fields include provider latency fields; topic latency itself is not measured. |
| GUI live state | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py::RuntimeObserver`, `api.py::runtime_live` | status/result topics -> live snapshot JSON | async subscriber + synchronous read | `partial` | medium for perceived UX | This is the user-visible path for live runtime sessions. |
| Artifact persistence | current live runtime path | per-segment state -> artifact | `missing` | n/a | Main observability gap: segmented/provider-stream runtime does not persist full per-segment trace artifacts like `RecognizeOnce` does. |

## D. Benchmark Execution Flow

Entrypoints:

- CLI: `scripts/run_benchmark_core.py`
- ROS action: `/benchmark/run_experiment` via `BenchmarkManagerNode`
- Gateway API: `POST /api/benchmark/run`

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| Run request entry | `scripts/run_benchmark_core.py`, `ros2_ws/src/asr_benchmark_nodes/asr_benchmark_nodes/benchmark_manager_node.py::_execute_benchmark`, `ros2_ws/src/asr_gateway/asr_gateway/api.py::benchmark_run` | CLI/action/API request -> `BenchmarkRunRequest` | sync CLI or async action/API wrapper | `partial` | low | Multiple entrypoints all converge on `BenchmarkOrchestrator.run()`. |
| Config resolution | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py::_resolve_run_plan` | benchmark/dataset/provider/metric profiles -> resolved run plan | synchronous | `good` | low | Run manifest includes config snapshot refs. |
| Artifact root creation | `.../orchestrator.py::run`, `ros2_ws/src/asr_storage/asr_storage/artifacts.py::make_benchmark_run` | run ID -> artifact directory tree | synchronous | `good` | low | Deterministic benchmark artifact structure exists. |
| Manifest persistence | `.../orchestrator.py::_build_run_manifest`, `ArtifactStore.save_manifest` | run plan -> `manifest/run_manifest.json` | synchronous | `good` | low | Includes scenario, provider execution, noise plan, config snapshots, environment. |
| Audio loading / noisy variant resolution | `.../orchestrator.py::_resolve_sample_audio_path`, `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py::apply_noise_to_wav` | sample + noise variant -> active WAV path | synchronous | `partial` | low to medium | Derived noisy WAVs are generated deterministically with stored SNR/seed. |
| Inference point | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py::run_sample` / `run_sample_streaming` | sample/provider pair -> normalized result row | synchronous | `good` | dominant | Provider call wrapped in `PipelineTraceCollector` stage. |
| Metrics creation point | `.../executor.py`, `ros2_ws/src/asr_metrics/asr_metrics/engine.py`, `summary.py` | result + reference -> per-row metrics + aggregate summary | synchronous | `good` | low | Computes quality, latency, reliability, cost, streaming, and resource metrics. |
| Trace export | `ros2_ws/src/asr_metrics/asr_observability/exporters/files.py::export_benchmark_trace` | trace -> JSON/CSV under run metrics | synchronous | `good` | low | Per-sample trace refs are stored in result rows. |
| Result persistence | `.../orchestrator.py::run` | results list -> `metrics/results.json`, `metrics/results.csv` | synchronous | `good` | low | Canonical raw benchmark outputs. |
| Summary/export persistence | `.../orchestrator.py::_build_summary`, `_export_reports_copy` | result rows -> `reports/summary.json`, `reports/summary.md`, `reports/benchmarks/<run_id>/*` | synchronous | `good` | low | Thesis-facing copy exists, but no single canonical benchmark matrix artifact is generated yet. |

## E. Noise Generation / Noisy Benchmark Flow

There are two distinct noise-related flows in the current codebase.

### E1. Runtime Noise Generation API

Entrypoint contract: `POST /api/runtime/generate_noise`

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| API entry | `ros2_ws/src/asr_gateway/asr_gateway/api.py::runtime_generate_noise` | source WAV + SNR list -> generation request | synchronous | `partial` | low | Measures total API duration and per-variant generation duration, but does not export a dedicated trace artifact. |
| Noise synthesis | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py::apply_noise_to_wav` | clean WAV -> noisy WAV | synchronous | `partial` | dominant in this flow | Deterministic by explicit `seed=1337` in API path. |
| Artifact persistence | `data/sample/generated_noise/*` | generated noisy WAVs | synchronous | `partial` | low | Files are written, but generation metadata is not persisted as a run manifest. |

### E2. Noisy Benchmark Flow

Entrypoint contract: benchmark scenario with non-clean noise plan

| Step | File / function / class | Input -> output | Sync / async | Instrumentation status | Suspected latency contribution | Notes |
|---|---|---|---|---|---|---|
| Noise plan resolution | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py::resolve_noise_plan` | scenario/profile settings -> noise variants | synchronous | `good` | low | Plan is persisted into benchmark run manifest. |
| Derived audio creation | `.../orchestrator.py::_resolve_sample_audio_path` + `apply_noise_to_wav` | clean sample -> derived noisy sample path | synchronous | `partial` | low to medium | Benchmark rows keep `noise_level`, `noise_mode`, `noise_snr_db`. |
| Inference + metrics | canonical benchmark flow D | noisy sample/provider -> result row and summary | synchronous | `good` | dominant | Quality can be grouped later under `noise_summary`. |
| Aggregate comparison | `.../orchestrator.py::_build_summary` | per-row noisy results -> `noise_summary` | synchronous | `good` | low | Clean vs noisy comparison exists, but current repo lacks a dedicated benchmark matrix export artifact. |

## Main Audit Conclusions

- `RecognizeOnce` is the best-instrumented runtime path today.
- Benchmark execution is the strongest reproducibility path because it persists a run manifest, config snapshots, per-row results, and trace artifacts.
- Live runtime sessions are still the weakest observability surface:
  - no persisted per-segment traces
  - no topic latency/drop metrics
  - no session-level resolved-config manifest
- The gateway is functionally correct but architecturally inefficient because request-scoped ROS nodes/executors add avoidable overhead.
