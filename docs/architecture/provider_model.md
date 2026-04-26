# Provider Model

## Summary

Provider packages are the canonical integration boundary for ASR engines.
Runtime, benchmark, and gateway code create providers through
`asr_provider_base.ProviderManager` using profile-driven configuration.

## Contract

- Input: `ProviderAudio`
- Lifecycle: `initialize()`, `validate_config()`, `recognize_once()`, optional streaming methods
- Output: `NormalizedAsrResult`
- Metadata: capabilities and runtime status come from `ProviderCapabilities` and `ProviderStatus`

## Active Providers

- `asr_provider_whisper`
- `asr_provider_vosk`
- `asr_provider_google`
- `asr_provider_azure`
- `asr_provider_aws`
- `asr_provider_huggingface`

## Rules

- New integrations belong in `asr_provider_*`, not in archived compatibility packages.
- Provider packages own SDK/session/auth helpers needed for runtime and gateway validation.
- Callers must stay provider-agnostic and use profiles plus normalized results.
