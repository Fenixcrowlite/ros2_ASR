# Providers

Provider adapters are implemented as ROS 2 Python packages under `ros2_ws/src/asr_provider_*`. Shared provider contracts and registry logic live in `ros2_ws/src/asr_provider_base`.

Use these pages together:

- [ASR backend activation reference](asr_backends.md) — exact commands for enabling every backend and links to official upstream documentation;
- [Provider environment setup](provider_env.md) — safe template and local configuration names for hosted and cloud services;
- [Provider-specific CLI checks](provider_cli.md) — terminal validation and real WAV transcription for the selected backend;
- this page — provider-specific expectations and troubleshooting notes.

## Which provider should be used first?

Use local Whisper for the first successful run:

```bash
make up PROVIDER_PROFILE=providers/whisper_local
```

Then verify the gateway and one bundled local transcription from another terminal:

```bash
cd ros2_ASR
make test-gateway-smoke
```

This path does not require a cloud account. The first transcription can take longer because the selected Whisper model may be downloaded and cached locally.

Use cloud providers only after the local flow works. That keeps ROS 2 and project problems separate from account, billing, IAM, and network problems.

## Available provider profiles

Profiles live under `configs/providers/`:

| Profile | Backend | Local or hosted | Additional setup |
| --- | --- | --- | --- |
| `providers/whisper_local` | faster-whisper | local | model downloads automatically on first use |
| `providers/vosk_local` | Vosk | local | run `make setup-vosk` |
| `providers/huggingface_local` | Hugging Face Transformers | local | optional Hub access for private or gated models |
| `providers/huggingface_api` | Hugging Face hosted inference | hosted | configure Hub access |
| `providers/azure_cloud` | Azure Speech | cloud | configure Speech resource key and region |
| `providers/google_cloud` | Google Cloud Speech-to-Text | cloud | enable API and configure Google authentication |
| `providers/aws_cloud` | Amazon Transcribe | cloud | configure AWS authentication, region, and writable S3 bucket |

Each profile declares an adapter import path, defaults, UI presets, advanced fields, and a credential reference.

## Validate a selected backend

After `make up` starts the gateway, choose either the browser UI or the terminal.

Browser UI:

1. open `http://127.0.0.1:8088`;
2. open the **Providers** page;
3. choose a provider profile and preset;
4. run validation;
5. run the bundled WAV test.

Terminal validation:

```bash
make provider-validate \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

Terminal WAV transcription:

```bash
make provider-test \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light \
  PROVIDER_WAV=data/sample/vosk_test.wav \
  PROVIDER_LANGUAGE=en-US
```

Replace the profile and preset with the backend you want to verify. Read [Provider-specific CLI checks](provider_cli.md) for examples.

`make test-gateway-smoke` is useful for the default local Whisper path and the gateway surface. It does not replace a provider-specific validation and WAV test for Vosk, Hugging Face, Azure, Google, or AWS.

## Local Whisper

Profile:

```text
providers/whisper_local
```

CPU presets:

```text
light
balanced
accurate
```

GPU presets:

```text
cuda_light
cuda_balanced
cuda_accurate
```

Use CPU preset `light` for the first run. Switch to a CUDA preset only after the CPU path works and the host has a working NVIDIA runtime.

Start the full stack:

```bash
make up PROVIDER_PROFILE=providers/whisper_local
```

## Local Vosk

Profile:

```text
providers/vosk_local
```

Download the optional English and Russian model folders plus the sample WAV:

```bash
make setup-vosk
```

Start Vosk:

```bash
make up PROVIDER_PROFILE=providers/vosk_local
```

Available presets:

```text
en_small
ru_small
```

If validation reports a missing model folder, rerun `make setup-vosk`.

## Local Hugging Face

Profile:

```text
providers/huggingface_local
```

The adapter uses a local `transformers.pipeline`. Public models can run without Hub access. Private or gated models may need local Hub configuration described in [Provider environment setup](provider_env.md).

Start the dedicated runtime profile:

```bash
make up RUNTIME_PROFILE=huggingface_local_runtime PROVIDER_PROFILE=providers/huggingface_local
```

Run the direct smoke check:

```bash
make hf-smoke-local
```

## Hugging Face hosted inference

Profile:

```text
providers/huggingface_api
```

Configure Hub access using [Provider environment setup](provider_env.md), then start the dedicated runtime profile:

```bash
make up RUNTIME_PROFILE=huggingface_api_runtime PROVIDER_PROFILE=providers/huggingface_api
```

Run the direct smoke check:

```bash
make hf-smoke-api
```

The provider advanced settings support a model ID, endpoint override, request timeout, timestamp mode, and generation parameters.

## Azure Speech

Profile:

```text
providers/azure_cloud
```

Create an Azure AI Speech resource, then configure the required local values described in [Provider environment setup](provider_env.md).

Start Azure:

```bash
make up PROVIDER_PROFILE=providers/azure_cloud
```

Open the **Providers** page, select preset `standard`, then run validation and the bundled WAV test.

## Google Cloud Speech-to-Text

Profile:

```text
providers/google_cloud
```

Enable Speech-to-Text for the selected Google Cloud project and configure either a service-account JSON file or Application Default Credentials as described in [Provider environment setup](provider_env.md).

Start Google:

```bash
make up PROVIDER_PROFILE=providers/google_cloud
```

Available presets:

```text
light       -> latest_short
balanced    -> default
accurate    -> latest_long
```

Open the **Providers** page, choose a preset, then run validation and the bundled WAV test.

## Amazon Transcribe

Profile:

```text
providers/aws_cloud
```

Configure AWS authentication, region, and a writable S3 bucket using [Provider environment setup](provider_env.md). Batch transcription uploads the WAV input to S3.

Start AWS:

```bash
make up PROVIDER_PROFILE=providers/aws_cloud
```

Open the **Providers** page, select preset `standard`, then run validation and the bundled WAV test.

A successful AWS login is not enough for batch mode when the configured S3 bucket is missing or not writable.

## Direct local smoke checks

```bash
source .venv/bin/activate
python3 scripts/run_provider_smoke_tests.py
```

## Expected clean-clone behavior

After `make setup` and `make build`:

- local Whisper validates without external account configuration;
- local Hugging Face validates for public models;
- Vosk validates after `make setup-vosk`;
- Hugging Face hosted inference validates after Hub access is configured;
- Azure validates after Speech resource configuration;
- Google validates after Google authentication is configured;
- AWS validates after AWS authentication, region, and bucket are configured.

Missing optional setup should produce a readable validation error, not a Python traceback.

## Add another provider

1. Add a package under `ros2_ws/src/asr_provider_<name>`.
2. Implement the shared provider contract from `asr_provider_base`.
3. Add package metadata and a smoke test.
4. Add a profile under `configs/providers/`.
5. Add a safe credential reference under `secrets/refs/` when needed.
6. Add tests for profile loading, result normalization, and failure handling.
7. Update `docs/asr_backends.md` and run `make docs-check`.
