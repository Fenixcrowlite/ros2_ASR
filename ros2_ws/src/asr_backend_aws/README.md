# asr_backend_aws (Legacy runtime wrapper)

Legacy AWS Transcribe backend retained for compatibility with the old
`asr_ros`-based runtime path.

## Status

This package is not the preferred integration point for new development.
Use `asr_provider_aws` for the modern provider-based runtime and benchmark
stack.

## Main Contents

- `asr_backend_aws/backend.py`: legacy `AwsAsrBackend` and streaming session
  implementation.

## Where It Is Still Relevant

- Compatibility tests.
- Legacy ROS node flows that still use `asr_core.models.AsrRequest` and
  `AsrResponse`.

## Boundary

- No provider registry integration.
- No normalized provider adapter contract.
