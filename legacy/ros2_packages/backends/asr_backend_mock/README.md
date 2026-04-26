# asr_backend_mock (Legacy runtime wrapper)

Deterministic mock backend used for compatibility paths, local smoke testing,
and scenarios where a predictable transcript is more important than real
inference.

## Main Contents

- `asr_backend_mock/backend.py`: `MockAsrBackend`.

## Typical Uses

- Legacy runtime tests.
- Fast smoke checks that should not depend on external SDKs or model files.
- Baseline flows where deterministic behavior is useful.

## Relationship To Modern Stack

This package follows the older backend contract from `asr_core`.
If a modern mock provider is needed, it should be added through
`asr_provider_base` rather than by extending this legacy wrapper.
