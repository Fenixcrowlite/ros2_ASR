# asr_provider_whisper

Canonical Whisper provider for runtime and benchmark execution.

## Contents

- `asr_provider_whisper/whisper_provider.py`: adapter entrypoint used by `ProviderManager`
- `asr_provider_whisper/backend.py`: provider-owned Whisper implementation details

## Scope

- local model/device validation
- one-shot recognition
- normalized degraded/error handling
