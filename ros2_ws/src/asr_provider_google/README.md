# asr_provider_google

Modern Google Speech adapter package for the provider-based runtime and
benchmark stack.

## Purpose

This package exposes Google Cloud Speech through the normalized provider
adapter API used by runtime orchestration and benchmark execution.

## Main Contents

- `asr_provider_google/google_provider.py`: `GoogleProvider`, the concrete
  adapter implementation.

## Relationship To Legacy Code

Use this package for new runtime/benchmark work.
The compatibility layer kept for older code is `asr_backend_google`.

## Typical Flow

1. `ProviderManager` resolves a provider profile.
2. `GoogleProvider` is instantiated and validated.
3. Runtime or benchmark code calls `recognize_once()` or streaming helpers.
4. The adapter returns a normalized provider result.

## Boundary

- No ROS node behavior.
- No UI logic.
- No benchmark planning.
