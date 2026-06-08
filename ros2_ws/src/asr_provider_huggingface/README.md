# asr_provider_huggingface

Hugging Face provider adapters for both local `transformers` inference and the
hosted Inference API.

## Purpose

This package gives the provider architecture two Hugging Face execution modes:

- local model execution through `transformers` and `torch`
- hosted HTTP inference through the Hugging Face Inference API

Both modes share the same normalized provider contract, so runtime and
benchmark code can switch between them through profiles instead of branching on
implementation details.

## Main Modules

- `asr_provider_huggingface/local_provider.py`:
  `HuggingFaceLocalProvider` for on-machine inference.
- `asr_provider_huggingface/api_provider.py`:
  `HuggingFaceAPIProvider` for hosted inference over HTTP.
- `asr_provider_huggingface/common.py`:
  shared audio conversion, token resolution, and normalized result builders.
- `asr_provider_huggingface/http_client.py`:
  minimal HTTP client and typed API error handling.

## Execution Modes

### Local mode

- Converts input audio into mono float32 waveforms.
- Builds a `transformers` ASR pipeline on demand.
- Can use CPU or GPU depending on configuration and local environment.

### API mode

- Sends WAV bytes to the configured Hugging Face inference endpoint.
- Uses token-based authentication resolved through credentials references.
- Normalizes the response into the same result model used by local mode.

## Typical Configuration Themes

- `model_id`
- device or dtype preferences for local inference
- endpoint/base URL and timeout values for API mode
- timestamp behavior and generation parameters where supported

## Boundary

- No ROS node orchestration.
- No benchmark planning.
