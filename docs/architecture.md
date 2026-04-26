# Architecture

## Canonical Layers

```mermaid
flowchart LR
  RT[asr_launch + asr_runtime_nodes] --> PB[asr_provider_base]
  PB --> P1[asr_provider_whisper]
  PB --> P2[asr_provider_vosk]
  PB --> P3[asr_provider_google]
  PB --> P4[asr_provider_azure]
  PB --> P5[asr_provider_aws]
  PB --> P6[asr_provider_huggingface]
  BM[asr_benchmark_core + asr_benchmark_nodes] --> PB
  GW[asr_gateway + web_ui] --> RT
  GW --> BM
  CORE[asr_core + asr_config + asr_datasets + asr_metrics + asr_storage + asr_reporting] --> RT
  CORE --> BM
  CORE --> GW
```

## Active Packages

- `asr_core`, `asr_config`, `asr_datasets`, `asr_metrics`, `asr_storage`, `asr_reporting`
- `asr_provider_base`, `asr_provider_*`
- `asr_runtime_nodes`, `asr_benchmark_core`, `asr_benchmark_nodes`
- `asr_gateway`, `asr_launch`, `web_ui`

## Archived Surface

- Historical runtime, benchmark, backend-wrapper packages, flat configs, and compatibility scripts live under top-level `legacy/`.
- They are not part of default `colcon`, `pytest`, `ruff`, `mypy`, or `make build` flows.

## Design Rules

- Runtime and benchmark select providers only through profile-driven configuration.
- Provider packages own provider implementation details and normalize outputs into `NormalizedAsrResult`.
- Gateway and UI talk to the canonical runtime and benchmark surfaces, not archived compatibility packages.
