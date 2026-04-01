from __future__ import annotations

from asr_config.validation import (
    validate_benchmark_payload,
    validate_metric_payload,
    validate_runtime_payload,
)


def test_validate_runtime_payload_rejects_invalid_runtime_shapes() -> None:
    errors = validate_runtime_payload(
        {
            "audio": {
                "source": "bluetooth",
                "sample_rate_hz": 0,
                "chunk_ms": -1,
                "file_replay_rate": -1,
                "mic_capture_sec": -1,
                "file_path": "",
            },
            "preprocess": {"target_sample_rate_hz": 0},
            "vad": {
                "energy_threshold": -1,
                "pre_roll_ms": -1,
                "max_silence_ms": -1,
                "min_segment_ms": 900,
                "max_segment_ms": 100,
            },
            "orchestrator": {
                "provider_profile": "",
                "processing_mode": "burst",
            },
            "session": {"max_concurrent_sessions": 0},
        }
    )

    assert "audio.source must be one of: file, mic (got 'bluetooth')" in errors
    assert "audio.sample_rate_hz must be > 0" in errors
    assert "audio.chunk_ms must be > 0" in errors
    assert "audio.file_replay_rate must be >= 0" in errors
    assert "audio.mic_capture_sec must be >= 0" in errors
    assert "preprocess.target_sample_rate_hz must be > 0" in errors
    assert "vad.energy_threshold must be >= 0" in errors
    assert "vad.min_segment_ms must be <= vad.max_segment_ms" in errors
    assert "runtime provider must be set via orchestrator.provider_profile or providers.active" in errors
    assert "orchestrator.processing_mode must be one of: segmented, provider_stream" in errors
    assert "session.max_concurrent_sessions must be > 0" in errors


def test_validate_runtime_payload_accepts_provider_selection_via_providers_active() -> None:
    errors = validate_runtime_payload(
        {
            "audio": {
                "source": "file",
                "sample_rate_hz": 16000,
                "chunk_ms": 500,
                "file_replay_rate": 1.0,
                "mic_capture_sec": 0.0,
                "file_path": "data/sample/vosk_test.wav",
            },
            "preprocess": {"target_sample_rate_hz": 16000},
            "vad": {
                "energy_threshold": 100,
                "pre_roll_ms": 250,
                "max_silence_ms": 700,
                "min_segment_ms": 400,
                "max_segment_ms": 2500,
            },
            "orchestrator": {
                "provider_profile": "",
                "processing_mode": "segmented",
            },
            "providers": {
                "active": "providers/huggingface_local",
                "preset": "balanced",
                "settings": {"device": "auto"},
            },
            "session": {"max_concurrent_sessions": 1},
        }
    )

    assert errors == []


def test_validate_benchmark_payload_rejects_invalid_runtime_controls() -> None:
    errors = validate_benchmark_payload(
        {
            "dataset_profile": "",
            "providers": ["providers/whisper_local", ""],
            "metric_profiles": [],
            "execution_mode": "interactive",
            "batch": {"max_samples": -1, "timeout_sec": 0},
            "streaming": {"chunk_ms": 0, "replay_rate": -1},
        }
    )

    assert "dataset_profile must be a non-empty string" in errors
    assert "providers entries must be non-empty strings" in errors
    assert "metric_profiles must be a non-empty list" in errors
    assert "execution_mode must be one of: batch, streaming" in errors
    assert "batch.max_samples must be >= 0" in errors
    assert "batch.timeout_sec must be > 0" in errors
    assert "streaming.chunk_ms must be > 0" in errors
    assert "streaming.replay_rate must be >= 0" in errors


def test_validate_benchmark_payload_allows_minimal_profile_with_implicit_defaults() -> None:
    errors = validate_benchmark_payload(
        {
            "dataset_profile": "datasets/sample_dataset",
            "providers": ["providers/whisper_local"],
            "metric_profiles": ["metrics/default_quality"],
        }
    )

    assert errors == []


def test_validate_metric_payload_rejects_unknown_metric_names() -> None:
    errors = validate_metric_payload({"metrics": ["wer", "unknown_metric"]})

    assert "Unknown metric: unknown_metric" in errors
