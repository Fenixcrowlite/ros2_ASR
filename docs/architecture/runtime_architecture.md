# Runtime Architecture

## Pipeline
1. `audio_input_node`
- Source abstraction: `file | mic`.
- Publishes `asr_interfaces/AudioChunk` to `/asr/runtime/audio/raw`.

2. `audio_preprocess_node`
- Mono conversion, resample, normalization.
- Publishes to `/asr/runtime/audio/preprocessed`.

3. `vad_segmenter_node`
- Energy-based VAD baseline.
- Publishes `SpeechActivity` and finalized `AudioSegment`.

4. `asr_orchestrator_node`
- Resolves runtime/provider profiles.
- Uses provider adapters via `asr_provider_base.ProviderManager`.
- Runs recognize-once on segments and publishes normalized partial/final outputs.
- Exposes runtime control services.

## Runtime control services
- `/asr/runtime/start_session` (`StartRuntimeSession`)
- `/asr/runtime/stop_session` (`StopRuntimeSession`)
- `/asr/runtime/reconfigure` (`ReconfigureRuntime`)
- `/asr/runtime/recognize_once` (`RecognizeOnce`)
- `/asr/runtime/list_backends` (`ListBackends`)
- `/config/list_profiles` (`ListProfiles`)
- `/config/validate` (`ValidateConfig`)
- `/asr/runtime/get_status` (`GetAsrStatus`)

## Runtime status topics
- `/asr/status/nodes`
- `/asr/status/sessions`
- `/asr/runtime/results/partial`
- `/asr/runtime/results/final`

## Lifecycle/composition note
Current baseline runs as separate nodes for clarity and debugability.
Architecture remains compatible with future composable deployment for low-latency local setups.
