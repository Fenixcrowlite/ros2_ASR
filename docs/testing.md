# Testing and Maintenance

## Documentation consistency

Run this after changing public setup guides, provider YAML profiles, credential-reference metadata, helper scripts, or the tracked environment template:

```bash
make docs-check
```

The check verifies that:

- every profile under `configs/providers/` appears in the public backend guide;
- local Markdown links resolve to tracked files;
- helper scripts pass syntax checks;
- the safe environment template contains the expected variable names and empty values only;
- the GNU Make public convenience layer is wired correctly;
- the documentation workflow watches the files that can affect public setup.

The same check runs automatically in GitHub Actions when relevant files change.

## Static public-release check

Before sharing the repository, run:

```bash
make public-release-check
```

This performs the documentation check, the secret scan, dataset portability validation, tracked-credential checks, and a safe-template check. It is intentionally static: it does not replace a clean-clone build or runtime test.

## Test targets

Fast Python tests:

```bash
make test-unit
```

ROS integration tests:

```bash
make test-ros
```

Colcon package tests:

```bash
make test-colcon
```

Full test target:

```bash
make test
```

`make test` starts with `make docs-check`, then runs Python and ROS-related checks. Run `make setup` before it.

Dataset validation:

```bash
make validate-datasets
```

## Gateway smoke test

Start the full stack first:

```bash
make up
```

Then run:

```bash
make test-gateway-smoke
```

This checks frontend routes, gateway endpoints, profile and secret validation responses, runtime start/reconfigure/stop behavior, preview audio, and one real local Whisper transcription of `data/sample/vosk_test.wav`.

Useful variants:

```bash
make test-gateway-smoke GATEWAY_URL=http://127.0.0.1:18088
make test-gateway-smoke GATEWAY_SMOKE_ARGS=--skip-recognition
```

The gateway smoke test is not a substitute for testing a selected Vosk, Hugging Face, Azure, Google, or AWS backend.

## Provider-specific gateway checks

Validate one selected backend through the running gateway API:

```bash
make provider-validate \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light
```

Run a real WAV transcription with that backend:

```bash
make provider-test \
  PROVIDER_PROFILE=providers/whisper_local \
  PROVIDER_PRESET=light \
  PROVIDER_WAV=data/sample/vosk_test.wav \
  PROVIDER_LANGUAGE=en-US
```

Replace the profile and preset with the backend you want to verify. For account-specific setup, read [Provider environment setup](provider_env.md). For activation commands, read [ASR backend activation reference](asr_backends.md).

Direct local smoke checks remain available:

```bash
source .venv/bin/activate
python3 scripts/run_provider_smoke_tests.py
```

Hugging Face shortcuts:

```bash
make hf-smoke-local
make hf-smoke-api
```

## Lint and type checks

```bash
make lint-ruff
make lint-mypy
make lint
```

Formatting:

```bash
make format
```

Security scan:

```bash
make security-scan
bash scripts/secret_scan.sh
```

## Local cleanup

```bash
make clean
```

This removes ROS build outputs, caches, local result/report directories, and runtime artifacts while keeping source files intact.

## Distribution helper

```bash
make dist
```

The distribution target cleans local outputs, checks public documentation, runs fast tests and a benchmark, performs release checks, scans for secrets, and creates a local distribution artifact.

## Test markers

Pytest markers are declared in `pyproject.toml`. The main groups are:

- `unit`
- `component`
- `contract`
- `api`
- `gui`
- `e2e`
- `integration`
- `regression`
- `slow`
- `cloud`
- `ros`

Use marker filters when working on a focused area:

```bash
source .venv/bin/activate
python -m pytest -q -m "api"
python -m pytest -q -m "not ros"
```

Some checks are environment-sensitive:

- ROS tests are skipped when ROS 2 Jazzy is not installed;
- the rqt environment check is skipped when `rqt` is not installed;
- cloud provider tests should mock provider authentication unless they are intentionally marked as real cloud integration tests.
