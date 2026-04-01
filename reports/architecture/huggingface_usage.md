# Hugging Face Usage

Updated: `2026-04-01`

This is the operator workflow for using the new Hugging Face integration through the unified provider system.

## 1. Install Runtime Dependencies

For local inference:

```bash
pip install -r requirements/providers-local.txt
```

This installs the packages required by `HuggingFaceLocalProvider`, including `transformers`, `accelerate`, and `torch`.

## 2. Configure Credentials

Local mode only needs `HF_TOKEN` for gated/private models. API mode requires it.

```bash
export HF_TOKEN=hf_your_token_here
```

Referenced secret files:

- `secrets/refs/huggingface_local_token.yaml`
- `secrets/refs/huggingface_api_token.yaml`

## 3. Select Provider by Config

Local runtime example:

```yaml
providers:
  active: providers/huggingface_local
  preset: balanced
  settings:
    device: auto
```

API runtime example:

```yaml
providers:
  active: providers/huggingface_api
  preset: balanced
  settings: {}
```

Shipped examples:

- `configs/runtime/huggingface_local_runtime.yaml`
- `configs/runtime/huggingface_api_runtime.yaml`
- `configs/providers/huggingface_local.yaml`
- `configs/providers/huggingface_api.yaml`

## 4. Run a Direct Smoke Test

Local mode:

```bash
python3 scripts/run_huggingface_smoke.py \
  --runtime-profile huggingface_local_runtime \
  --reference-text "hello world"
```

API mode:

```bash
python3 scripts/run_huggingface_smoke.py \
  --runtime-profile huggingface_api_runtime \
  --reference-text "hello world"
```

The script prints:

- transcript text
- latency breakdown
- provider metadata
- provider runtime metrics
- optional WER/CER if `--reference-text` is supplied

## 5. Run Through the Web UI

Start the gateway-first stack:

```bash
./scripts/run_web_ui.sh
```

In the Runtime page:

1. choose `providers/huggingface_local` or `providers/huggingface_api`
2. choose a preset such as `light`, `balanced`, or `accurate`
3. optionally override advanced settings in JSON
4. upload or select a WAV file
5. click `Transcribe Whole File`

Observed flow:

- GUI calls `/api/runtime/recognize_once`
- gateway forwards to ROS2 `/asr/runtime/recognize_once`
- orchestrator loads the selected provider dynamically
- result and metrics return to the same runtime page

## 6. Run a Benchmark Matrix

Example benchmark profile:

- `configs/benchmark/huggingface_provider_matrix.yaml`

Run it with:

```bash
python3 scripts/run_benchmark_core.py \
  --benchmark-profile huggingface_provider_matrix
```

This compares:

- `providers/huggingface_local`
- `providers/huggingface_api`

Metrics remain comparable with other providers because all adapters return `NormalizedAsrResult`.

## 7. Add a New Provider Without Code Changes to the Runtime

Option A: add a provider profile with an adapter path:

```yaml
profile_id: providers/custom_remote
provider_id: custom_remote
adapter: my_pkg.providers.CustomRemoteProvider
settings: {}
```

Option B: inject a plugin through environment:

```bash
export ASR_PROVIDER_PLUGIN_MODULES="custom_remote=my_pkg.providers.CustomRemoteProvider"
```

After that, the provider becomes selectable through the same manager, catalog, and runtime workflow.
