# Newbie Code Guide

This guide explains the project structure and "who calls whom" in plain language.

## 1. Main Runtime Flow

1. `audio_capture_node` captures microphone (or WAV file fallback) and publishes raw PCM chunks to `/asr/audio_chunks`.
2. `asr_server_node` subscribes to `/asr/audio_chunks`, buffers chunks, and flushes them after short silence.
3. `asr_server_node` calls selected backend (`whisper`, `vosk`, `google`, `aws`, `azure`, or `mock`) via unified `asr_core` API.
4. Final normalized result is published to `/asr/text`.
5. Metrics are collected and published to `/asr/metrics`.

## 2. Core Modules

- `asr_core/models.py`: shared request/response dataclasses.
- `asr_core/backend.py`: abstract backend interface + default streaming fallback.
- `asr_core/factory.py`: backend registry and dynamic creation by name.
- `asr_core/config.py`: YAML/ENV merge and normalization utilities.

## 3. ROS Entry Points

- Service `/asr/recognize_once`: one-shot WAV transcription.
- Service `/asr/set_backend`: switch backend at runtime.
- Service `/asr/get_status`: current backend and capability flags.
- Action `/asr/transcribe`: long-running/stream-like request path.
- Topic `/asr/text`: final ASR messages.
- Topic `/asr/metrics`: quality/performance telemetry.

## 4. Backends

- `mock`: deterministic fake backend for tests/CI.
- `vosk`: local offline ASR with native streaming.
- `whisper`: local high-quality ASR via faster-whisper.
- `google`, `aws`, `azure`: real cloud integrations using SDKs.

All backends return the same `AsrResponse` schema.

## 5. Important Config Files

- `configs/default.yaml`: safe default profile (`mock` backend, benchmark scenarios).
- `configs/live_mic_whisper.yaml`: live microphone + whisper `large-v3`.
- `configs/commercial.example.yaml`: cloud credentials template (copy to local untracked file).

## 6. Tests

- Unit tests: `make test-unit`.
- ROS integration tests: `make test-ros`.
- Cloud tests are marked `@pytest.mark.cloud` and skipped without credentials.
- Benchmark scenarios support list or comma-separated string; unsupported labels fail early.
- Dataset relative WAV paths are resolved manifest-first for reproducible runs.

## 7. CI

Workflow file: `.github/workflows/ci.yml`.

Current CI pipeline does:
1. install dependencies,
2. run `ruff check .`,
3. run `pytest -m "not cloud and not ros" -q`.

So CI is fast and stable by default (no cloud billing, no ROS runtime dependency).

## 8. Cloud Auth and Safety Gates

When a Web GUI run targets cloud backends, startup is fail-fast:

1. `google` requires a readable service-account JSON file.
2. `azure` requires `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`.
3. `aws` requires `AWS_PROFILE` or a native access-key pair, plus provider-side `s3_bucket`.
4. `aws` runs STS preflight before long jobs (boto3-first, CLI fallback if boto3 is unavailable).
5. Common AWS SSO failures are normalized to actionable messages (expired pending authorization, invalid grant, expired token).

This design prevents long ROS runs that are guaranteed to fail due to auth issues.

## 9. ROS Shutdown Behavior

ROS node entry points now guard shutdown with context checks before calling `rclpy.shutdown()`.
This prevents noisy double-shutdown tracebacks (`rcl_shutdown already called`) when stopping bringup jobs or pressing `Ctrl+C`.

## 10. Background Activity and Screen Wakeups

Build/test flows now blocklist colcon desktop notifications by default via:

`COLCON_EXTENSION_BLOCKLIST=colcon_core.event_handler.desktop_notification`

This reduces accidental screen wakeups from background automation runs.

Colcon-heavy flows also run through a shared lock wrapper (`scripts/with_colcon_lock.sh`),
so parallel starts of build/test/demo/bench do not race on the same workspace directories.

Web GUI keeps a local draft of non-secret form fields in browser storage,
so you do not need to re-fill backend/model run settings after each restart.

Jobs from previous sessions that are already inactive are moved into a collapsed dropdown list,
while active jobs stay pinned in the main table.

AWS STS auth preflight now uses a short in-memory success cache (default 120s),
so repeated AWS job starts do not re-run identical auth checks on every click.
