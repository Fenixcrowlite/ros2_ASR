# Provider Model

## Adapter contract (`asr_provider_base.AsrProviderAdapter`)
- `initialize(config, credentials_ref)`
- `validate_config()`
- `discover_capabilities()`
- `recognize_once(audio, options)`
- `start_stream(options)`
- `push_audio(chunk)`
- `stop_stream()`
- `get_status()`
- `teardown()`

## Capability model
- `supports_streaming`
- `supports_batch`
- `supports_word_timestamps`
- `supports_partials`
- `supports_confidence`
- `supports_language_auto_detect`
- `supports_cpu`
- `supports_gpu`
- `requires_network`
- `cost_model_type`
- `max_session_seconds`
- `max_audio_seconds`

## Implemented adapters
- Local baseline working: `WhisperProvider`
- Cloud baseline working: `AzureProvider`
- Additional adapters/scaffolding: `VoskProvider`, `GoogleProvider`, `AwsProvider`

`WhisperProvider` now reports honest degraded/error outcomes when decoding fails or returns an empty transcript for non-silent audio. Runtime and benchmark paths do not substitute mock transcripts.

## Legacy integration strategy
New adapters reuse stable logic from legacy `asr_backend_*` packages via wrapper mapping.
This minimizes rewrite risk while establishing clean boundaries for future native adapter implementations.
