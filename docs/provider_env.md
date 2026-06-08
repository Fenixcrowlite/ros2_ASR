# Provider Environment Setup

Cloud and hosted ASR backends use local configuration values that must stay outside version control.

## Create the local environment file

Use the safe initializer:

```bash
make init-provider-env
nano secrets/local/runtime.env
```

The Make target calls `scripts/init_provider_env.sh`. The initializer copies the tracked template only when `secrets/local/runtime.env` does not exist, applies file mode `600`, and keeps an existing configuration unchanged.

Manual equivalent:

```bash
mkdir -p secrets/local
cp configs/runtime.env.example secrets/local/runtime.env
chmod 600 secrets/local/runtime.env
nano secrets/local/runtime.env
```

Fill only the sections for the providers you plan to use. Leave unused values empty. Never commit `secrets/local/runtime.env`.

The runtime scripts load this file automatically.

## Azure Speech

Required names:

```text
AZURE_SPEECH_KEY
AZURE_SPEECH_REGION
```

Optional endpoint override:

```text
ASR_AZURE_ENDPOINT
```

Official setup guide:

```text
https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-to-text
```

## Hugging Face

Required for hosted inference and for private or gated Hub models:

```text
HF_TOKEN
```

Official token guide:

```text
https://huggingface.co/docs/hub/security-tokens
```

## Google Cloud Speech-to-Text

Use one of the authentication paths described in the Google guide. For an explicit JSON file path, configure:

```text
GOOGLE_APPLICATION_CREDENTIALS
```

When the project cannot be inferred automatically, also configure:

```text
GOOGLE_CLOUD_PROJECT
```

Official setup and authentication guides:

```text
https://cloud.google.com/speech-to-text/docs/setup
https://cloud.google.com/docs/authentication/provide-credentials-adc
```

## Amazon Transcribe

Recommended AWS CLI profile configuration:

```text
AWS_PROFILE
AWS_REGION
AWS_S3_BUCKET
```

The project also accepts these bucket aliases for compatibility:

```text
ASR_AWS_S3_BUCKET
AWS_TRANSCRIBE_BUCKET
```

Batch transcription requires a writable S3 bucket.

Official guides:

```text
https://docs.aws.amazon.com/transcribe/latest/dg/getting-started.html
https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html
https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html
```

## Validate the configured provider

Start the stack with the selected provider profile, open `http://127.0.0.1:8088`, then use the **Providers** page to run validation and the bundled WAV test.

For terminal validation and real WAV transcription, read [Provider-specific CLI checks](provider_cli.md).

For activation commands for every backend, read [ASR backend activation reference](asr_backends.md).
