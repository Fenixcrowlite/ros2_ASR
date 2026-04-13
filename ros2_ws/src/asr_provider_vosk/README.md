# asr_provider_vosk

Modern Vosk adapter package for the provider-based runtime and benchmark stack.

## Purpose

This package provides an offline/local ASR option through the common provider
contract, making Vosk usable in the same runtime and benchmark flows as cloud
providers.

## Main Contents

- `asr_provider_vosk/vosk_provider.py`: `VoskProvider`, the concrete adapter.

## Characteristics

- Local inference, suitable for offline experiments.
- Exposed through the same `asr_provider_base` lifecycle as other providers.
- Intended for both runtime pipelines and benchmark comparison runs.

## Relationship To Legacy Code

Use `asr_provider_vosk` for new development.
The legacy wrapper package is `asr_backend_vosk`.

## Boundary

- No ROS pipeline orchestration.
- No benchmark artifact persistence.
