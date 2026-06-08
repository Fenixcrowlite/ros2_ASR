# ASR Backend Activation Reference

This reference lists every ASR backend included in the project, the official upstream documentation, and the exact project command used to enable it.

Read [Provider environment setup](provider_env.md) for the safe local template and account-specific variable names. Read [Providers](providers.md) for provider-specific expectations. Start with local Whisper before configuring hosted services.

## Local Whisper

Project profile: `providers/whisper_local`

Official documentation:

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/openai/whisper

Start the full stack:

```bash
make up PROVIDER_PROFILE=providers/whisper_local
```

Minimal ROS 2 runtime:

```bash
make up-runtime PROVIDER_PROFILE=providers/whisper_local
```

The first model load may download a local checkpoint. Use preset `light` for the first run.

## Vosk

Project profile: `providers/vosk_local`

Official documentation:

- https://alphacephei.com/vosk/install
- https://alphacephei.com/vosk/models
- https://github.com/alphacep/vosk-api

Prepare local models:

```bash
make setup-vosk
```

Start the full stack:

```bash
make up PROVIDER_PROFILE=providers/vosk_local
```

Minimal ROS 2 runtime:

```bash
make up-runtime PROVIDER_PROFILE=providers/vosk_local
```

## Hugging Face local

Project profile: `providers/huggingface_local`

Official documentation:

- https://huggingface.co/docs/transformers/tasks/asr
- https://huggingface.co/docs/hub/security-tokens
- https://huggingface.co/models?pipeline_tag=automatic-speech-recognition

Start with the dedicated runtime profile:

```bash
make up RUNTIME_PROFILE=huggingface_local_runtime PROVIDER_PROFILE=providers/huggingface_local
```

Run the direct smoke check:

```bash
make hf-smoke-local
```

## Hugging Face API

Project profile: `providers/huggingface_api`

Official documentation:

- https://huggingface.co/docs/hub/security-tokens
- https://huggingface.co/docs/inference-providers/index
- https://huggingface.co/docs/inference-endpoints/index

Start with the dedicated runtime profile:

```bash
make up RUNTIME_PROFILE=huggingface_api_runtime PROVIDER_PROFILE=providers/huggingface_api
```

Run the direct smoke check:

```bash
make hf-smoke-api
```

## Azure Speech

Project profile: `providers/azure_cloud`

Official documentation:

- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-to-text
- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/

Start the full stack after completing the Azure setup described in [Provider environment setup](provider_env.md):

```bash
make up PROVIDER_PROFILE=providers/azure_cloud
```

## Google Cloud Speech-to-Text

Project profile: `providers/google_cloud`

Official documentation:

- https://cloud.google.com/speech-to-text/docs/setup
- https://cloud.google.com/speech-to-text/docs/transcribe-client-libraries
- https://cloud.google.com/docs/authentication/provide-credentials-adc
- https://cloud.google.com/iam/docs/keys-create-delete

Start the full stack after completing the Google setup described in [Provider environment setup](provider_env.md):

```bash
make up PROVIDER_PROFILE=providers/google_cloud
```

## Amazon Transcribe

Project profile: `providers/aws_cloud`

Official documentation:

- https://docs.aws.amazon.com/transcribe/latest/dg/getting-started.html
- https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html

Start the full stack after completing the AWS setup described in [Provider environment setup](provider_env.md):

```bash
make up PROVIDER_PROFILE=providers/aws_cloud
```

## Verify the selected backend

After the stack starts, open:

```text
http://127.0.0.1:8088
```

Use the **Providers** page to select the active profile, choose a preset, run validation, and execute the bundled WAV test.

The same checks are available from the terminal.

Validate the selected profile:

```bash
make provider-validate \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

Run a real WAV transcription:

```bash
make provider-test \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light \
  PROVIDER_WAV=data/sample/vosk_test.wav \
  PROVIDER_LANGUAGE=en-US
```

Replace the profile and preset with the backend you want to verify. For more examples and optional variables, read [Provider-specific CLI checks](provider_cli.md).

`make test-gateway-smoke` verifies the gateway surface and performs a default local Whisper transcription. It does not replace a provider-specific test for Vosk, Hugging Face, Azure, Google, or AWS.
