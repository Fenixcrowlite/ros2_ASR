from __future__ import annotations

from asr_core.models import AsrResponse, AsrTimings
from asr_metrics.collector import MetricsCollector

from scripts.live_sample_eval import (
    backend_model_region,
    backend_target_label,
    collect_live_record,
    detect_interfaces,
    parse_backend_model_spec,
    parse_csv_values,
    resolve_backend_targets,
)


def test_parse_csv_values() -> None:
    assert parse_csv_values(" core, ros_service ,,ros_action ") == [
        "core",
        "ros_service",
        "ros_action",
    ]


def test_detect_interfaces_unknown_raises() -> None:
    try:
        detect_interfaces("core,invalid")
    except ValueError as exc:
        assert "Unknown interfaces" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid interface")


def test_backend_model_region_prefers_backend_values() -> None:
    cfg = {
        "asr": {"model": "default-model", "region": "default-region"},
        "backends": {
            "whisper": {"model_size": "large-v3"},
            "google": {"model": "latest_long", "region": "global"},
        },
    }
    model_w, region_w = backend_model_region(cfg, "whisper")
    assert model_w == "large-v3"
    assert region_w == "default-region"

    model_g, region_g = backend_model_region(cfg, "google")
    assert model_g == "latest_long"
    assert region_g == "global"


def test_parse_backend_model_spec() -> None:
    assert parse_backend_model_spec("whisper:large-v3@local") == (
        "whisper",
        "large-v3",
        "local",
    )
    assert parse_backend_model_spec("mock") == ("mock", "", "")


def test_resolve_backend_targets_from_model_runs() -> None:
    cfg = {
        "asr": {"backend": "mock", "model": "", "region": ""},
        "backends": {"whisper": {"model_size": "base"}, "mock": {}},
    }
    targets = resolve_backend_targets(
        cfg=cfg,
        cli_backends="",
        cli_model_runs="whisper:tiny,mock,whisper:tiny",
    )
    labels = [backend_target_label(item) for item in targets]
    assert labels == ["whisper:tiny", "mock"]


def test_collect_live_record_without_reference_marks_unknown_quality() -> None:
    collector = MetricsCollector(pricing_per_minute={"mock": 0.0})
    response = AsrResponse(
        text="hello world",
        language="en-US",
        success=True,
        timings=AsrTimings(preprocess_ms=1.0, inference_ms=2.0, postprocess_ms=1.0),
        audio_duration_sec=1.0,
        backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
    )
    record = collect_live_record(
        collector=collector,
        backend_label="mock",
        interface="core",
        wav_path="data/sample/en_hello.wav",
        language="en-US",
        reference_text="",
        response=response,
    )
    assert record.wer == -1.0
    assert record.cer == -1.0
    assert record.transcript_ref == ""
