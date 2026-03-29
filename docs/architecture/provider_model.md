# Provider Model

## Adapter contract (`asr_provider_base.AsrProviderAdapter`)
- `initialize(config, credentials_ref)`
- `validate_config()`
- `discover_capabilities()`
- `recognize_once(audio, options)`
- `start_stream(options)`
- `push_audio(chunk)`
- `drain_stream_results()`
- `stop_stream()`
- `get_status()`
- `teardown()`

## Capability model
- `supports_streaming`
- `streaming_mode` (`none | simulated | native`)
- `supports_batch`
- `supports_word_timestamps`
- `supports_partials`
- `supports_confidence`
- `supports_language_auto_detect`
- `supports_cpu`
- `supports_gpu`
- `requires_network`
- `cost_model_type`
- `max_session_seconds`
- `max_audio_seconds`

## Implemented adapters
- Local baseline working: `WhisperProvider`
- Cloud baselines working with native streaming path where credentials are valid:
  - `GoogleProvider`
  - `AzureProvider`
  - `AwsProvider`
- Additional adapter: `VoskProvider`

`WhisperProvider` now reports honest degraded/error outcomes when decoding fails or returns an empty transcript for non-silent audio. Runtime and benchmark paths do not substitute mock transcripts.

## Native streaming status
- `vosk`: native local streaming with partial results.
- `google`: native cloud gRPC streaming (`streaming_recognize`) with interim results and aggregated final.
- `azure`: native cloud push-stream continuous recognition with interim results and aggregated final.
- `aws`: native cloud `StartStreamTranscription` path with partial results and aggregated final.
- `whisper`: no provider-stream support in the runtime contract. It is exposed as batch / recognize-once only until a real incremental decoding path exists.

Cloud adapters fail fast when required credentials are absent or expired. They do not silently downgrade to buffered pseudo-streaming.

## Native cloud auth nuance

### Google
- Uses the native Google service-account JSON file.
- The gateway validates that the referenced file exists and is readable.

### Azure
- Uses native environment-backed auth:
  - `AZURE_SPEECH_KEY`
  - `AZURE_SPEECH_REGION`
  - optional `ASR_AZURE_ENDPOINT`
- The gateway reports missing env vars directly in `Secrets`.
- The platform also supports a local env-injection file at `secrets/local/runtime.env`.
  - It stores native env var names only.
  - It is git-ignored.
  - GUI setup writes to this file instead of provider YAML.
  - Runtime/provider initialization reads it through the same `env` secret-ref model, so GUI-assisted setup stays architecture-safe and does not invent a provider-specific credential wrapper.

### AWS
- Uses native AWS auth, not a project-specific wrapper file.
- The platform supports:
  - `AWS_PROFILE` backed by shared AWS config / IAM Identity Center (SSO)
  - or native access keys (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN`)
- For IAM Identity Center / SSO there are two separate moving parts:
  1. the sign-in session in `~/.aws/sso/cache`
  2. the temporary role credentials used by SDK calls in `~/.aws/cli/cache`

This distinction matters because runtime and benchmark jobs may still work while role credentials remain valid even after the sign-in session has already expired. The gateway therefore exposes AWS auth as structured state instead of a single boolean. GUI users can see:
- whether the profile uses SSO
- whether the sign-in session is still valid
- whether role credentials are still valid for runtime/benchmark use
- which action is recommended next

The GUI `Secrets` page can also start a native `aws sso login` flow through the gateway so the operator can recover directly from an expired sign-in session.

## Legacy integration strategy
One-shot cloud and local adapters continue to reuse stable logic from `asr_backend_*` packages.
Native cloud streaming is implemented as backend-owned stream sessions surfaced through the provider contract, so runtime and benchmark layers stay provider-agnostic while using real SDK streaming semantics.
