# asr_backend_google (Legacy runtime wrapper)

Legacy Google Cloud Speech backend kept for compatibility with the older
runtime layer.

## Status

For new code, use `asr_provider_google`.
This package is the historical backend implementation that predates the modern
provider abstraction.

## Main Contents

- `asr_backend_google/backend.py`: legacy `GoogleAsrBackend` and related
  streaming support.

## Boundary

- No provider adapter metadata or capability model.
- No benchmark-oriented normalized provider interface.
