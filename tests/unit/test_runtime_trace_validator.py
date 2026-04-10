from __future__ import annotations

from asr_observability.models import PipelineTrace, StageTrace
from asr_observability.validators.runtime import validate_trace


def _stage(*, started_ns: int, ended_ns: int, name: str = "provider_recognize") -> StageTrace:
    return StageTrace(
        stage=name,
        component="test",
        code_path="tests.unit.test_runtime_trace_validator",
        started_ns=started_ns,
        ended_ns=ended_ns,
        duration_ms=max((ended_ns - started_ns) / 1_000_000.0, 0.0),
        wall_started_at="2026-03-31T00:00:00+00:00",
        wall_finished_at="2026-03-31T00:00:00+00:00",
    )


def test_validate_trace_allows_wer_and_cer_above_one_when_non_negative() -> None:
    trace = PipelineTrace(
        trace_id="trace_demo",
        trace_type="runtime_recognize_once",
        created_at="2026-03-31T00:00:00+00:00",
        metrics_semantics_version=1,
        request_id="req_1",
        session_id="session_1",
        provider_id="whisper",
        started_ns=0,
        finished_ns=3_000_000,
        total_duration_ms=3.0,
        stages=[_stage(started_ns=0, ended_ns=1_000_000)],
        metrics={
            "audio_load_ms": 0.0,
            "preprocess_ms": 0.0,
            "inference_ms": 1.0,
            "postprocess_ms": 0.0,
            "total_latency_ms": 1.0,
            "ros_service_latency_ms": 1.0,
            "time_to_result_ms": 1.0,
            "real_time_factor": 0.5,
            "wer": 1.5,
            "cer": 2.25,
        },
    )

    report = validate_trace(trace)

    assert report.valid is True
    assert report.corrupted is False
    assert report.errors == []


def test_validate_trace_rejects_negative_wer() -> None:
    trace = PipelineTrace(
        trace_id="trace_negative",
        trace_type="runtime_recognize_once",
        created_at="2026-03-31T00:00:00+00:00",
        metrics_semantics_version=1,
        request_id="req_2",
        session_id="session_2",
        provider_id="whisper",
        started_ns=0,
        finished_ns=3_000_000,
        total_duration_ms=3.0,
        stages=[_stage(started_ns=0, ended_ns=1_000_000)],
        metrics={
            "audio_load_ms": 0.0,
            "preprocess_ms": 0.0,
            "inference_ms": 1.0,
            "postprocess_ms": 0.0,
            "total_latency_ms": 1.0,
            "ros_service_latency_ms": 1.0,
            "time_to_result_ms": 1.0,
            "real_time_factor": 0.5,
            "wer": -0.1,
        },
    )

    report = validate_trace(trace)

    assert report.valid is False
    assert "Metric `wer` must be >= 0" in report.errors
