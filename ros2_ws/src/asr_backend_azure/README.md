# asr_backend_azure (Legacy runtime wrapper)

Legacy Azure Speech backend retained for compatibility with the older
`asr_ros` runtime path.

## Status

New development should target `asr_provider_azure`.
This package exists so legacy flows can continue to work while the repository
finishes migrating to the provider adapter architecture.

## Main Contents

- `asr_backend_azure/backend.py`: legacy `AzureAsrBackend` and streaming logic.

## Boundary

- No `ProviderManager` integration.
- No normalized provider adapter API.
