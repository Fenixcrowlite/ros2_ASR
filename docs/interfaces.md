# Interfaces

Актуальный интерфейсный контракт для modular ROS2 runtime stack.

## Terms

- Runtime: live ASR pipeline (`audio_input -> preprocess -> VAD -> orchestrator`).
- Provider profile: YAML profile из `configs/providers/*.yaml`.
- Runtime profile: YAML profile из `configs/runtime/*.yaml`.
- Session: управляемый runtime run, который стартует через `/asr/runtime/start_session`.
- One-shot: единичная транскрипция WAV через `/asr/runtime/recognize_once`.

## Topics

- `/asr/runtime/audio/raw` (`asr_interfaces/msg/AudioChunk`)
- `/asr/runtime/audio/preprocessed` (`asr_interfaces/msg/AudioChunk`)
- `/asr/runtime/vad/activity` (`asr_interfaces/msg/SpeechActivity`)
- `/asr/runtime/audio/segments` (`asr_interfaces/msg/AudioSegment`)
- `/asr/runtime/results/partial` (`asr_interfaces/msg/AsrResultPartial`)
- `/asr/runtime/results/final` (`asr_interfaces/msg/AsrResult`)
- `/asr/status/nodes` (`asr_interfaces/msg/NodeStatus`)
- `/asr/status/sessions` (`asr_interfaces/msg/SessionStatus`)
- `/benchmark/status` (`asr_interfaces/msg/BenchmarkJobStatus`)
- `/benchmark/events` (`asr_interfaces/msg/BenchmarkEvent`)

## Message: `AsrResult.msg`

Ключевые поля:

- `request_id`
- `text`
- `confidence`
- `word_timestamps`
- `language`
- `backend`
- `model`
- `region`
- `total_ms`
- `is_final`
- `success`
- `error_code`
- `error_message`
- `session_id`
- `provider_id`
- `is_partial`
- `degraded`

Это основной structured output контракт для runtime final results.

## Message: `AsrResultPartial.msg`

Используется для partial results в streaming/provider-stream mode.

Ключевые поля:

- `request_id`
- `text`
- `session_id`
- `provider_id`
- `language`
- `first_partial_latency_ms`

## Services

### `/asr/runtime/start_session` (`StartRuntimeSession.srv`)

Request:

- `runtime_profile`
- `provider_profile`
- `provider_preset`
- `provider_settings_json`
- `session_id`
- `runtime_namespace`
- `auto_start_audio`
- `processing_mode`
- `audio_source`
- `audio_file_path`
- `language`
- `mic_capture_sec`

Response:

- `accepted`
- `session_id`
- `message`
- `resolved_config_ref`

### `/asr/runtime/stop_session` (`StopRuntimeSession.srv`)

Request:

- `session_id`

Response:

- `success`
- `message`

### `/asr/runtime/reconfigure` (`ReconfigureRuntime.srv`)

Request:

- `session_id`
- `runtime_profile`
- `provider_profile`
- `provider_preset`
- `provider_settings_json`
- `processing_mode`
- `audio_source`
- `audio_file_path`
- `language`
- `mic_capture_sec`

Response:

- `success`
- `message`
- `resolved_config_ref`

### `/asr/runtime/recognize_once` (`RecognizeOnce.srv`)

Request:

- `wav_path`
- `language`
- `enable_word_timestamps`
- `session_id`
- `provider_profile`
- `provider_preset`
- `provider_settings_json`

Response:

- `result` (`AsrResult`)
- `resolved_profile`

`provider_profile` в `RecognizeOnce` может override текущий runtime provider для
одного запроса без перестройки активной live session.

### `/asr/runtime/list_backends` (`ListBackends.srv`)

Response:

- `provider_ids`

### `/asr/runtime/get_status` (`GetAsrStatus.srv`)

Response:

- `backend`
- `model`
- `region`
- `capabilities`
- `streaming_supported`
- `streaming_mode`
- `cloud_credentials_available`
- `status_message`
- `session_id`
- `session_state`
- `processing_mode`
- `audio_source`
- `runtime_profile`

### `/config/list_profiles` (`ListProfiles.srv`)

Request:

- `profile_type`

Response:

- `profile_ids`

### `/config/validate` (`ValidateConfig.srv`)

Request:

- `profile_type`
- `profile_id`
- `config_path`

Response:

- `valid`
- `message`
- `resolved_config_ref`

## Actions

### `/benchmark/run_experiment` (`RunBenchmarkExperiment`)

Goal:

- `benchmark_profile`
- `dataset_profile`
- `providers`
- `scenario`
- `provider_overrides_json`
- `benchmark_settings_json`
- `run_id`

Result:

- `run_id`
- `success`
- `message`
- benchmark summary

## Capability model

Provider capabilities определяются adapter layer, а не docs вручную.
Ключевые флаги:

- `supports_streaming`
- `streaming_mode`
- `supports_batch`
- `supports_word_timestamps`
- `supports_partials`
- `supports_confidence`
- `supports_language_auto_detect`
- `requires_network`
- `cost_model_type`

Для runtime truth source используй:

- `/asr/runtime/get_status`
- `/asr/runtime/list_backends`
- `GET /api/providers/catalog`
- `POST /api/providers/validate`

## Legacy compatibility note

`/asr/set_backend`, `/asr/get_status`, `/asr/text/plain` и связанные `asr_ros`
interfaces больше не являются primary contract для modular runtime stack.
Они оставлены только как compatibility surface и migration reference.
