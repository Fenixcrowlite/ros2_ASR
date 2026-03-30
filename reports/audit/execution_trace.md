# Execution Trace

Trace source: isolated run `thesis_20260330_self_audit_final` on `ROS_DOMAIN_ID=93`.

## 1. `RecognizeOnce` service

Input:
- WAV: `data/sample/vosk_test.wav`
- provider profile: `providers/whisper_local`
- preset: `balanced`
- language: `en-US`

Output:
- text: `1-0-0-0-1 9-0-2-1-0 0-1-8-0-3`
- confidence: `0.8086`
- audio duration: `8.308 s`
- trace: `artifacts/runtime_sessions/thesis_20260330_self_audit_final_recognize_once/metrics/trace_8569f6b8f47b42e9abd9bdffacc0f7e9.json`

| Step | Input | Output | Time | Location |
|---|---|---|---:|---|
| Frontend request build | selected WAV + provider settings | JSON POST body | client-side only | `web_ui/frontend/js/pages/runtime.js:473` |
| HTTP API entry | `RecognizeRequest` | ROS service call | included below | `ros2_ws/src/asr_gateway/asr_gateway/api.py:2349` |
| ROS service bridge | service request | JSON payload | `service_wait_ms=0.03`, `service_call_ms=1913.80`, `gateway_request_ms=1914.17` | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py:568` |
| Audio load stage | `wav_path` | `265914` bytes, `8.308 s` duration | `0.69 ms` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:1128` |
| Provider inference stage | `ProviderAudio` | Whisper transcript + timings | `1765.08 ms` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:1202` |
| Result publish/return | normalized result | ROS topic + HTTP response | total ASR latency `1765.01 ms`, trace wall time `1768.91 ms` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:1260` and `:735` |

Latency breakdown from trace:
- `preprocess_ms=848.59`
- `inference_ms=916.34`
- `postprocess_ms=0.08`
- `total_latency_ms=1765.01`
- `time_to_result_ms=1768.91`
- `real_time_factor=0.2124`

## 2. GUI-triggered runtime session

Input:
- runtime profile: `default_runtime`
- provider profile: `providers/whisper_local`
- preset: `light`
- audio source: `file`
- audio file: `data/sample/vosk_test.wav`

Observed output:
- first published final transcript: `100001`
- confidence: `0.6932`
- segment audio duration: `2.5 s`
- API wall time to result: `4032.65 ms`

| Step | Input | Output | Time | Location |
|---|---|---|---:|---|
| Frontend start request | runtime payload | POST `/api/runtime/start` | client-side only | `web_ui/frontend/js/api.js:63` |
| HTTP runtime start | validated runtime + provider profile | ROS `StartRuntimeSession` call | `service_call_ms=43.33` | `ros2_ws/src/asr_gateway/asr_gateway/api.py:2236` |
| Orchestrator session setup | runtime request | reconfigure sibling nodes + activate session | inside start call | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:939` |
| Audio input start | WAV file path | `AudioChunk` stream on raw audio topic | file source worker starts immediately | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_input_node.py:500` |
| Preprocess stage | `AudioChunk` | mono/resampled/normalized `AudioChunk` | per chunk, not exported as first-class trace | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/audio_preprocess_node.py:97` |
| VAD stage | preprocessed chunk stream | speech segment flush | first flush at `max_segment_ms=2500` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/vad_segmenter_node.py:176` and `:268` |
| Provider segment inference | `AudioSegment` | final transcript `100001` | `latency_ms=978.39` | `ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py:668` and `:735` |
| Gateway live polling | final result topic | `/api/runtime/live` snapshot | first result visible at `4032.65 ms` wall time | `ros2_ws/src/asr_gateway/asr_gateway/ros_client.py:347` |

Runtime result latency breakdown:
- `audio_duration_sec=2.5`
- `preprocess_ms=555.04`
- `inference_ms=417.43`
- `postprocess_ms=5.93`
- `latency_ms=978.39`

Finding:
- On the same source WAV, the segmented runtime path produced `100001`, while direct `RecognizeOnce` produced the full number sequence. The difference is caused by VAD-driven chunking and not by service transport.

## 3. Noise generation flow

Input:
- source WAV: `data/sample/vosk_test.wav`
- SNR levels: `30 dB`, `10 dB`

Output:
- `data/sample/generated_noise/vosk_test_snr30p0_3.wav`
- `data/sample/generated_noise/vosk_test_snr10p0_3.wav`

| Step | Input | Output | Time | Location |
|---|---|---|---:|---|
| Frontend request | source WAV + SNR list | POST `/api/runtime/generate_noise` | client-side only | `web_ui/frontend/js/api.js:62` |
| API entry | `NoiseGenerateRequest` | generated variants list | total `603.83 ms` | `ros2_ws/src/asr_gateway/asr_gateway/api.py:2141` |
| Variant generation `30 dB` | source WAV | `vosk_test_snr30p0_3.wav` | `175.33 ms` | `ros2_ws/src/asr_gateway/asr_gateway/api.py:2154` |
| Variant generation `10 dB` | source WAV | `vosk_test_snr10p0_3.wav` | `175.24 ms` | `ros2_ws/src/asr_gateway/asr_gateway/api.py:2154` |
| DSP implementation | PCM frames | noisy PCM frames | included above | `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/noise.py` |

Note:
- The total API time is higher than the two per-variant timings because catalog refresh and WAV metadata extraction are included in the endpoint total.
