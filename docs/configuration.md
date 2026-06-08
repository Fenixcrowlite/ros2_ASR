# Configuration

Configuration is profile-driven. Profiles are YAML or JSON files under `configs/`, grouped by runtime area.

## Directory map

- `configs/runtime`: audio, preprocessing, VAD, orchestration, and session profiles.
- `configs/providers`: provider adapter and preset profiles.
- `configs/benchmark`: benchmark suites and execution settings.
- `configs/datasets`: dataset profile metadata.
- `configs/metrics`: quality, timing, observability, thresholds, and scoring.
- `configs/deployment`: local deployment presets.
- `configs/gui`: browser UI defaults.
- `configs/resolved`: local runtime snapshots.

## Profile IDs

Profiles use stable IDs such as:

```yaml
profile_id: runtime/default
```

Make targets usually accept the file-stem form:

```bash
make up-runtime RUNTIME_PROFILE=default_runtime
make up PROVIDER_PROFILE=providers/whisper_local
make bench-suite BENCHMARK_PROFILE=default_benchmark
```

## Secret references

Provider profiles use `credentials_ref` to point at local reference metadata. The files under `secrets/refs/` are tracked because they describe where a value comes from, not the value itself.

Local providers without account configuration use:

```yaml
credentials_ref: secrets/refs/local_none.yaml
```

Hosted and cloud providers resolve local values from environment variables or:

```text
secrets/local/runtime.env
```

Create the local file safely:

```bash
make init-provider-env
nano secrets/local/runtime.env
```

The Make target copies `configs/runtime.env.example` only when the local file does not exist, applies file mode `600`, and preserves an existing configuration.

Manual equivalent:

```bash
mkdir -p secrets/local
cp configs/runtime.env.example secrets/local/runtime.env
chmod 600 secrets/local/runtime.env
nano secrets/local/runtime.env
```

Fill only the providers you use. Leave unused values empty. Never commit `secrets/local/runtime.env`.

For the canonical variable list, accepted compatibility aliases, and official provider-side setup guides, read [Provider environment setup](provider_env.md).

A Google service-account JSON file can also live at:

```text
secrets/google/service-account.json
```

That path is ignored and must not be committed.

## Validation

Check public documentation and provider-profile coverage:

```bash
make docs-check
```

Run dataset validation:

```bash
make validate-datasets
```

Validate profile files directly:

```bash
python3 scripts/validate_configs/validate_profile.py --type runtime --id default_runtime
python3 scripts/validate_configs/validate_profile.py --type providers --id whisper_local
```

Validate the running gateway surface after `make up`:

```bash
make test-gateway-smoke
```

Validate a selected ASR backend:

```bash
make provider-validate \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

Run a real WAV transcription with that backend:

```bash
make provider-test \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

For more provider-check variables, read [Provider-specific CLI checks](provider_cli.md).

Before publishing changes, run the static public-release check:

```bash
make public-release-check
```

## Local outputs

Resolved configs, run artifacts, logs, reports, and build products are local outputs. They are intentionally ignored so source control contains only reproducible project inputs.
