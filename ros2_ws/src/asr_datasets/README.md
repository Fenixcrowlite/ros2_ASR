# asr_datasets

Dataset registry/import/manifest subsystem.

## Responsibilities
- Normalize dataset manifest format.
- Validate dataset samples.
- Import datasets from folder/manifest.
- Maintain dataset registry metadata.

## Boundaries
- No runtime inference.
- No benchmark orchestration (handled by benchmark core).
