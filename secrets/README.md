# Secrets Directory

This directory intentionally contains only non-secret reference definitions.

The files under `secrets/refs/*.yaml` describe where runtime credentials come from, but they do not contain credential values.

Keep real credential material out of Git:

- `secrets/local/runtime.env` for local environment-variable injection;
- `secrets/google/service-account.json` for a Google service-account JSON file;
- native provider configuration files such as `~/.aws/config` and `~/.aws/credentials`.

## Create the local runtime file

Use the safe initializer:

```bash
make init-provider-env
nano secrets/local/runtime.env
```

The Make target copies the tracked empty template only when `secrets/local/runtime.env` does not exist, applies file mode `600`, and keeps an existing local configuration unchanged.

Manual equivalent:

```bash
mkdir -p secrets/local
cp configs/runtime.env.example secrets/local/runtime.env
chmod 600 secrets/local/runtime.env
nano secrets/local/runtime.env
```

Fill only the providers you use. Leave unused values empty. Never commit `secrets/local/runtime.env`.

The canonical variable list and provider-side setup links live in:

```text
docs/provider_env.md
```

## Validate local configuration

Use the browser UI **Secrets** page after `make up` starts. For backend-specific terminal validation and a real WAV transcription, read:

```text
docs/provider_cli.md
```

For backend activation commands, read:

```text
docs/asr_backends.md
```
