# asr_provider_aws

Canonical AWS Transcribe provider for the runtime, benchmark, and gateway stacks.

## Contents

- `asr_provider_aws/aws_provider.py`: adapter entrypoint used by `ProviderManager`
- `asr_provider_aws/backend.py`: provider-owned AWS implementation details and streaming session helpers

## Scope

- profile-driven initialization
- config validation
- one-shot recognition
- native streaming

No ROS node logic, benchmark orchestration, or HTTP routing lives here.
