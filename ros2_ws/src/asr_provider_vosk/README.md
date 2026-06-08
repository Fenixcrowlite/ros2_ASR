# asr_provider_vosk

Canonical local/offline Vosk provider for runtime and benchmark execution.

## Contents

- `asr_provider_vosk/vosk_provider.py`: adapter entrypoint used by `ProviderManager`
- `asr_provider_vosk/backend.py`: provider-owned Vosk model/session helpers

## Scope

- local model validation
- one-shot recognition
- native streaming
