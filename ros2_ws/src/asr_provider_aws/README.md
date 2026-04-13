# asr_provider_aws

Modern AWS Transcribe adapter package for the provider-based runtime and
benchmark stack.

## Purpose

This package exposes AWS as an `asr_provider_base.AsrProviderAdapter`
implementation so it can participate in:

- `asr_runtime_nodes` live inference
- `asr_benchmark_core` benchmark execution
- `asr_gateway` provider validation and catalog flows

## Main Contents

- `asr_provider_aws/aws_provider.py`: `AwsProvider`, the modern adapter.

## Relationship To Legacy Code

`asr_provider_aws` is the package new code should target.
It wraps or reuses behavior from the legacy package `asr_backend_aws`, but
presents the normalized provider contract expected by the new architecture.

## Boundary

- No ROS node logic.
- No benchmark scheduling.
- No gateway routing.
