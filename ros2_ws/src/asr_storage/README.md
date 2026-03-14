# asr_storage

Artifact and manifest persistence layer.

## Responsibilities
- Manage artifact roots and run/session directories.
- Save run manifests, raw/normalized outputs, metrics, and reports.
- Return artifact references with checksum metadata.

## Boundaries
- No metric calculations.
- No provider-specific logic.
