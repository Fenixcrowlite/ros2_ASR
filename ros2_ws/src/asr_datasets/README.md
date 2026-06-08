# asr_datasets

Dataset manifest, registry, and import helpers used by the benchmark subsystem
and the gateway.

## Purpose

This package gives the rest of the workspace a stable representation of "what a
dataset is" without coupling callers to raw CSV folders or ad-hoc JSON.

It standardizes:

- sample metadata
- manifest loading/saving
- dataset registration
- importing datasets from folders or uploaded files

## Main Responsibilities

- Define the canonical `DatasetSample` manifest row model.
- Validate required fields such as `sample_id`, `audio_path`, `transcript`,
  and `language`.
- Resolve manifest-relative audio paths deterministically.
- Create and maintain a dataset registry through `DatasetRegistry`.
- Import datasets either from an existing manifest or by scanning a folder.

## Key Modules

- `asr_datasets/manifest.py`: dataset sample model, manifest validation,
  `load_manifest`, and `save_manifest`.
- `asr_datasets/registry.py`: `DatasetEntry` and `DatasetRegistry`.
- `asr_datasets/importer.py`: folder and upload based dataset import helpers.

## Manifest Expectations

The current manifest loader reads one JSON object per line (`.jsonl` style).
Each sample should include at least:

- `sample_id`
- `audio_path`
- `transcript`
- `language`

Optional fields such as `duration_sec`, `split`, `tags`, and `metadata` are
preserved and used later by benchmark/reporting code.

## Consumers

- `asr_benchmark_core` uses dataset manifests as the unit-of-work source.
- `asr_benchmark_nodes` exposes import and registration over ROS.
- `asr_gateway` uses the registry for API/UI dataset management.

## Boundary Rules

- No inference or ASR provider logic.
- No benchmark scheduling.
- No report rendering.
