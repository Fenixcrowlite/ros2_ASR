# Pipeline Map

Audit baseline: `thesis_20260330_self_audit_final` on `2026-03-30`.

## Runtime GUI -> backend -> ROS2 -> ASR -> output

### 1. Direct "Recognize Once" path

1. The Runtime page collects the selected WAV, language, provider profile, preset, and advanced provider settings in `recognizeOnce()` at `web_ui/frontend/js/pages/runtime.js:473`.
2. The frontend posts JSON to `/api/runtime/recognize_once` through `runtimeRecognizeOnce()` in `web_ui/frontend/js/api.js:66`.
3. FastAPI validates the selected provider profile and sample path, then calls the ROS bridge in `ros2_ws/src/asr_gateway/asr_gateway/api.py:2349`.
4. `GatewayRosClient.recognize_once()` builds a `RecognizeOnce` service request, measures service wait and service call time, and returns a JSON-ready payload in `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py:568`.
5. The runtime service `/asr/runtime/recognize_once` is hosted by `AsrOrchestratorNode` in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:176`.
6. The orchestrator direct path:
   - loads WAV bytes in `_on_recognize_once()` via `_read_recognize_audio_bytes()` at `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:1107`
   - measures `audio_load`
   - calls the provider adapter `recognize_once()`
   - builds and validates a runtime trace
   - copies the result into the service response
   - publishes the same result on the final result topic
7. Provider inference happens inside the selected provider adapter, for Whisper in `ros2_ws/src/asr_provider_whisper/asr_provider_whisper/whisper_provider.py:95`.
8. Results return to the user in three places:
   - HTTP response payload from `/api/runtime/recognize_once`
   - ROS topic publish from `_publish_result()` at `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:735`
   - gateway observer snapshot used by `/api/runtime/live`
9. Trace artifacts for this path are written to `artifacts/runtime_sessions/<session_id>/metrics/trace_*.json`.

### 2. Runtime session path

1. The Runtime page sends `runtimePayload()` to `/api/runtime/start` in `web_ui/frontend/js/pages/runtime.js`.
2. FastAPI validates the runtime and provider profile, then calls `GatewayRosClient.start_runtime()` in `ros2_ws/src/asr_gateway/asr_gateway/api.py:2236`.
3. The orchestrator accepts `/asr/runtime/start_session` in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:160`.
4. During start, the orchestrator:
   - reconfigures preprocess, VAD, and audio input services through `_call_service()` at `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:467`
   - activates the session
   - starts the audio source through `/asr/runtime/audio/start_session`
5. `AudioInputNode` streams WAV bytes into `AudioChunk` messages on the raw audio topic in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py:487`.
6. `AudioPreprocessNode` converts channel layout, resamples, normalizes, and republishes the chunk in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py:97`.
7. `VadSegmenterNode` consumes preprocessed chunks, publishes speech activity, buffers speech, and flushes `AudioSegment` messages in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py:176`.
8. `AsrOrchestratorNode._on_segment()` runs provider inference on each segment and publishes final results in `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:668` and `:735`.
9. The gateway observer consumes the final result topic and exposes it through `/api/runtime/live`.

### 3. Noise generation path

1. The Runtime page sends `source_wav` and `snr_levels` to `/api/runtime/generate_noise` from `web_ui/frontend/js/pages/runtime.js:499`.
2. FastAPI resolves the runtime sample, calls `apply_noise_to_wav()`, records per-variant and total generation time, then refreshes the runtime sample catalog in `ros2_ws/src/asr_gateway/asr_gateway/api.py:2141`.
3. The actual perturbation is applied in `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py`.
4. Generated files are written to `data/sample/generated_noise/`.

## Benchmark path

1. Benchmark runs are planned and executed by `BenchmarkOrchestrator` in `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py:104`.
2. The orchestrator resolves dataset, provider, metric, and noise plans in `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py:311`.
3. `BatchExecutor.run_sample()` and `run_sample_streaming()` execute provider calls, evaluate metrics, build traces, and sample system metrics in `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py:50` and `:195`.
4. Reports are copied to thesis-facing outputs under `reports/benchmarks/<run_id>/` in `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py:585`.

## Where key work happens

- Audio file selection/loading:
  - frontend sample picker: `web_ui/frontend/js/pages/runtime.js`
  - backend path resolution: `ros2_ws/src/asr_gateway/asr_gateway/api.py:2361`
  - direct WAV byte load: `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:1138`
  - streamed file source: `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py:500`
- Inference:
  - provider adapters: `ros2_ws/src/asr_provider_*/`
  - benchmark executor provider calls: `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/executor.py:104`
- Result return:
  - ROS service response: `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py:587`
  - ROS topic publish: `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:735`
  - HTTP payload: `ros2_ws/src/asr_gateway/asr_gateway/api.py:2372`
  - benchmark files: `reports/benchmarks/<run_id>/summary.json`, `summary.md`, `results.json`, `results.csv`
