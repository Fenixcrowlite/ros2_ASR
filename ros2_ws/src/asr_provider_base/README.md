# asr_provider_base

Provider adapter contract, registry, catalog metadata, and profile-driven
provider construction.

## Purpose

This package is the abstraction layer between runtime/benchmark orchestration
code and concrete ASR providers such as Whisper, Vosk, Azure, Google, AWS, or
Hugging Face.

It allows the rest of the workspace to ask for "a provider selected by this
profile" without importing any provider-specific SDKs directly.

## Main Responsibilities

- Define the `AsrProviderAdapter` lifecycle contract.
- Define normalized provider-side models such as `ProviderAudio`,
  `ProviderStatus`, and `ProviderMetadata`.
- Describe provider capabilities in a machine-readable way.
- Register and instantiate adapters through the provider registry.
- Resolve provider profiles, presets, overrides, and credentials through
  `ProviderManager`.
- Expose UI/catalog metadata used by the gateway and config-driven selection.

## Key Modules

- `asr_provider_base/adapter.py`: abstract adapter lifecycle and streaming API.
- `asr_provider_base/models.py`: request/status/metadata/runtime-metric models.
- `asr_provider_base/capabilities.py`: provider capability matrix.
- `asr_provider_base/registry.py`: provider registration and instantiation.
- `asr_provider_base/manager.py`: profile-driven adapter creation with secrets.
- `asr_provider_base/catalog.py`: UI metadata, presets, and execution presets.
- `asr_provider_base/config/provider_selection.py`: runtime payload provider
  selection helpers.
- `asr_provider_base/adapters/normalization.py`: convert legacy backend outputs
  into canonical normalized results.
- `asr_provider_base/providers/plugins.py`: optional plugin discovery support.

## Lifecycle

The common adapter flow is:

1. Resolve provider profile and optional preset.
2. Load credentials through `asr_config`.
3. Instantiate the adapter from the registry.
4. Call `initialize()` and `validate_config()`.
5. Run `recognize_once()` or the streaming methods.
6. Read status/metadata/metrics when needed.
7. Call `teardown()` when done.

## Used By

- `asr_runtime_nodes` for live runtime inference.
- `asr_benchmark_core` for batch and streaming benchmark execution.
- `asr_gateway` for provider catalog, validation, and on-demand checks.
- Concrete provider packages in `asr_provider_*`.

## Boundary Rules

- No ROS node behavior.
- No FastAPI routing.
- No benchmark scheduling logic.
- No provider-specific SDK initialization outside concrete adapters.
