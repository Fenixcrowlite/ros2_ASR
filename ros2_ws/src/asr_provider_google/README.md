# asr_provider_google

Canonical Google Speech provider for the runtime, benchmark, and gateway stacks.

## Contents

- `asr_provider_google/google_provider.py`: adapter entrypoint used by `ProviderManager`
- `asr_provider_google/backend.py`: provider-owned Google implementation and streaming helpers

## Scope

- profile-driven initialization
- credential/file validation
- one-shot recognition
- native streaming
