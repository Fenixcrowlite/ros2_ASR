# asr_backend_vosk (Legacy runtime wrapper)

Legacy Vosk backend retained for compatibility with the older runtime path.

## Status

Use `asr_provider_vosk` for the modern provider-based architecture.
This package remains for backwards compatibility with code that still expects
the legacy backend contract.

## Main Contents

- `asr_backend_vosk/backend.py`: legacy `VoskAsrBackend`.

## Characteristics

- Local/offline inference.
- Older request/response model based on `asr_core.models`.
