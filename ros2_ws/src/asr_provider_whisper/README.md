# asr_provider_whisper

Whisper adapter implementation for local ASR baseline.

- Wraps legacy `asr_backend_whisper` runtime logic.
- Exposes unified adapter contract from `asr_provider_base`.
- Returns honest degraded/error results when Whisper cannot decode non-silent audio.
- Does not substitute mock transcripts in runtime or benchmark paths.
