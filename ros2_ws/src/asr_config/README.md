# asr_config

Profile-driven configuration loading, validation, and secret reference
resolution for the whole ASR stack.

## Purpose

This package turns YAML profiles and secret reference files into typed,
resolved payloads that the runtime nodes, gateway, provider manager, and
benchmark orchestrator can consume consistently.

It is the configuration glue between human-edited files under `configs/` and
the code that needs fully resolved settings at runtime.

## Main Responsibilities

- Resolve profile files by type and profile ID.
- Merge layered YAML structures into a deterministic final payload.
- Validate runtime, benchmark, and metric configuration payloads before they
  reach ROS nodes or HTTP handlers.
- Load secret references and resolve them from environment variables or local
  `.env`-style files.
- Produce configuration snapshots suitable for storage in benchmark artifacts.

## Key Modules

- `asr_config/loader.py`: profile lookup, merge order, and resolved snapshot
  generation.
- `asr_config/models.py`: typed config/secret dataclasses.
- `asr_config/secrets.py`: secret-ref loading and environment/file resolution.
- `asr_config/validation.py`: structural validation for runtime, benchmark, and
  metric payloads.

## Expected Inputs

- YAML profiles under a `configs_root`, usually the repository `configs/`
  directory.
- Optional secret reference files that point to environment variables or
  local secret material.

Typical profile groups used by the rest of the workspace include:

- runtime profiles
- provider profiles
- benchmark profiles
- dataset profiles
- metric profiles

## Consumers

- `asr_runtime_nodes`: runtime profile loading and reconfiguration validation.
- `asr_provider_base`: provider profile resolution and credential loading.
- `asr_benchmark_core`: benchmark/dataset/metric profile resolution.
- `asr_gateway`: API-side validation and secret state inspection.

## Boundary Rules

- No provider SDK imports.
- No ROS topic or service logic.
- No HTTP routing.
- No benchmark execution.

## Practical Notes

- Validation helpers return a list of human-readable errors instead of raising
  immediately. This makes them usable from the gateway UI and ROS services.
- Secret resolution is intentionally centralized here so provider adapters do
  not need to know repository-specific secret storage conventions.
