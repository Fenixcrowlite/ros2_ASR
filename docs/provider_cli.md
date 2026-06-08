# Provider-Specific CLI Checks

Use these commands after the gateway stack has started:

```bash
make up
```

The Make targets call `scripts/provider_gateway_check.py` and verify the ASR backend you explicitly selected rather than the default local Whisper path.

## Validate a provider profile

```bash
make provider-validate \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

## Run a real WAV transcription

```bash
make provider-test \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light \
  PROVIDER_WAV=data/sample/vosk_test.wav \
  PROVIDER_LANGUAGE=en-US
```

Replace the profile and preset with the backend you want to verify.

Examples:

```bash
make provider-validate PROVIDER_PROFILE=providers/vosk_local PROVIDER_PRESET=en_small
make provider-validate PROVIDER_PROFILE=providers/huggingface_local PROVIDER_PRESET=light
make provider-validate PROVIDER_PROFILE=providers/huggingface_api PROVIDER_PRESET=balanced
make provider-validate PROVIDER_PROFILE=providers/azure_cloud PROVIDER_PRESET=standard
make provider-validate PROVIDER_PROFILE=providers/google_cloud PROVIDER_PRESET=balanced
make provider-validate PROVIDER_PROFILE=providers/aws_cloud PROVIDER_PRESET=standard
```

Hosted and cloud providers must be configured first. Read [Provider environment setup](provider_env.md) and [ASR backend activation reference](asr_backends.md).

## Common variables

```text
GATEWAY_URL             gateway URL, default http://127.0.0.1:8088
PROVIDER_PROFILE        provider profile ID
PROVIDER_PRESET         provider preset ID
PROVIDER_WAV            WAV file used by provider-test
PROVIDER_LANGUAGE       language tag, default en-US
PROVIDER_SETTINGS_JSON  advanced provider override object
PROVIDER_CHECK_ARGS     additional helper arguments
```

## Difference from the gateway smoke test

`make test-gateway-smoke` verifies browser routes, gateway endpoints, runtime controls, and one default local Whisper transcription.

`make provider-validate` and `make provider-test` verify the backend you explicitly selected. Use them when testing Vosk, Hugging Face, Azure, Google, or AWS.
