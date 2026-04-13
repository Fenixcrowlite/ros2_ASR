# asr_backend_whisper (Legacy runtime wrapper)

Legacy Whisper backend retained for compatibility with the pre-provider
runtime path.

## Status

For new runtime or benchmark integration, use `asr_provider_whisper`.
This package is the compatibility layer around the older backend contract.

## Main Contents

- `asr_backend_whisper/backend.py`: legacy `WhisperAsrBackend`.

## Typical Use Today

- Legacy `asr_ros` compatibility.
- Migration support while newer nodes use the provider adapter contract.
