# asr_storage

Artifact layout and persistence helpers for runtime sessions, benchmark runs,
comparisons, and exported reports.

## Purpose

This package owns the filesystem structure under the ASR artifact root. Other
packages ask it for directories and save helpers instead of hard-coding folder
trees throughout the codebase.

## Main Responsibilities

- Create runtime session directories under `runtime_sessions/`.
- Create benchmark run directories under `benchmark_runs/`.
- Persist JSON, text, metrics, manifests, and report artifacts.
- Return `ArtifactRef` objects with path, checksum, size, and inferred run ID.

## Directory Model

`ArtifactStore` creates and manages these top-level areas:

- `runtime_sessions/`
- `benchmark_runs/`
- `comparisons/`
- `exports/`
- `temp/`

For benchmark runs it standardizes subdirectories such as:

- `manifest/`
- `resolved_configs/`
- `raw_outputs/`
- `normalized_outputs/`
- `metrics/`
- `reports/`
- `logs/`

## Key Modules

- `asr_storage/artifacts.py`: `ArtifactStore` and the directory/save helpers.
- `asr_storage/models.py`: `ArtifactRef` metadata model used by reports and UI.

## Consumers

- `asr_benchmark_core` uses it to persist run manifests, metrics, and reports.
- `asr_gateway` reads artifact trees indirectly when building result views.
- `asr_reporting` writes exported report files into the artifact tree.

## Boundary Rules

- No benchmark metric computation.
- No dataset import logic.
- No provider-specific behavior.
- No HTTP or ROS code.

## Practical Guidance

If a new subsystem needs to store files, prefer extending `ArtifactStore`
instead of inventing a new folder structure elsewhere. That keeps the gateway
and report readers consistent.
