# asr_provider_azure

Canonical Azure Speech provider for the runtime, benchmark, and gateway stacks.

## Contents

- `asr_provider_azure/azure_provider.py`: adapter entrypoint used by `ProviderManager`
- `asr_provider_azure/backend.py`: provider-owned Azure SDK integration and streaming helpers

## Scope

- profile-driven initialization
- credential-aware validation
- one-shot recognition
- native streaming
