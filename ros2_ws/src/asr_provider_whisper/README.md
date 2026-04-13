# asr_provider_whisper

Modern Whisper adapter package for the provider-based runtime and benchmark
stack.

## Purpose

This package exposes Whisper through the normalized provider adapter API used
by the modern runtime pipeline and benchmark subsystem.

## Main Contents

- `asr_provider_whisper/whisper_provider.py`: `WhisperProvider`, the adapter.

## Behavioral Notes

- Wraps the legacy Whisper backend behavior behind the modern provider
  interface.
- Returns honest degraded/error outputs instead of silently substituting mock
  transcripts.
- Is suitable as a local baseline provider for runtime and benchmark flows.

## Relationship To Legacy Code

New code should use `asr_provider_whisper`.
The compatibility backend package is `asr_backend_whisper`.

## Boundary

- No ROS node code.
- No benchmark scheduling.
