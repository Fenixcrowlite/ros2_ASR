# Interfaces

## Terms

- Backend: ASR implementation provider (`mock`, `vosk`, `whisper`, `google`, `aws`, `azure`).
- Streaming: incremental recognition from audio chunks.
- WER/CER: word/character error rates against reference transcript.
- RTF: `processing_time / audio_duration` (lower is better).
- Lifecycle node: node with explicit configure/activate-like runtime state transitions.

## Topics

- `/asr/audio_chunks` (`std_msgs/msg/UInt8MultiArray`): PCM audio chunks (mono int16) consumed by `asr_server_node` for live streaming/fallback recognition.
- `/asr/text` (`asr_interfaces/msg/AsrResult`): final/partial transcription result.
- `/asr/metrics` (`asr_interfaces/msg/AsrMetrics`): runtime and quality telemetry.

## Message: `WordTimestamp.msg`

- `word` (`string`): recognized token.
- `start_sec` (`float32`): word start in seconds.
- `end_sec` (`float32`): word end in seconds.
- `confidence` (`float32`): per-word confidence if available.

## Message: `AsrResult.msg`

- `header` (`std_msgs/Header`): ROS timestamp/frame metadata.
- `request_id` (`string`): request correlation id.
- `text` (`string`): final hypothesis.
- `partials` (`string[]`): partial hypotheses (streaming).
- `confidence` (`float32`): normalized confidence when provider exposes it.
- `word_timestamps` (`WordTimestamp[]`): optional aligned words.
- `language` (`string`): requested/detected language.
- `backend` (`string`): provider id.
- `model` (`string`): provider model name.
- `region` (`string`): cloud region or `local`.
- `audio_duration_sec` (`float32`): input audio duration.
- `preprocess_ms` (`float32`): preprocessing latency.
- `inference_ms` (`float32`): provider/backend latency.
- `postprocess_ms` (`float32`): normalization/packaging latency.
- `total_ms` (`float32`): full processing time.
- `is_final` (`bool`): final result flag.
- `success` (`bool`): operation success flag.
- `error_code` (`string`): normalized error code.
- `error_message` (`string`): provider error details (sanitized).

## Message: `AsrMetrics.msg`

- `header`, `request_id`, `backend`.
- `wer`, `cer`, `rtf`, `latency_ms`.
- `cpu_percent`, `ram_mb`, `gpu_util_percent`, `gpu_mem_mb`.
- `cost_estimate`: estimated cloud cost by configured pricing.
- `success`, `notes`.

## Services

### `/asr/recognize_once` (`RecognizeOnce.srv`)

Request:
- `wav_path` (`string`)
- `language` (`string`)
- `enable_word_timestamps` (`bool`)

Response:
- `result` (`AsrResult`)

### `/asr/set_backend` (`SetAsrBackend.srv`)

Request:
- `backend` (`string`)
- `model` (`string`)
- `region` (`string`)

Response:
- `success` (`bool`)
- `message` (`string`)

### `/asr/get_status` (`GetAsrStatus.srv`)

Response:
- `backend`, `model`, `region`
- `capabilities` (`string[]`)
- `streaming_supported` (`bool`)
- `cloud_credentials_available` (`bool`)
- `status_message` (`string`)

## Action

### `/asr/transcribe` (`Transcribe.action`)

Goal:
- `wav_path` (`string`)
- `language` (`string`)
- `streaming` (`bool`)
- `chunk_sec` (`float32`)

Feedback:
- `partial_result` (`AsrResult`)
- `metrics` (`AsrMetrics`)

Result:
- `result` (`AsrResult`)

## Capabilities Matrix

| Backend | recognize_once | streaming | word timestamps | confidence |
|---|---|---|---|---|
| `mock` | yes | real (deterministic) | yes | yes |
| `vosk` | yes | real | yes | yes |
| `whisper` | yes | simulated fallback | yes | yes |
| `google` | yes | simulated fallback | yes | yes |
| `aws` | yes | simulated fallback | yes | yes |
| `azure` | yes | simulated fallback | yes | yes |

Notes:
- Simulated streaming means chunks are accepted and action feedback is produced, but final text comes from one-shot/fallback processing.
- Use `/asr/get_status` to read runtime capabilities (`streaming_mode`, `word_timestamps`, `confidence`, cloud credential availability).
