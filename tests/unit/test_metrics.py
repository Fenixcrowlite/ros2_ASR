from asr_core.models import AsrResponse, AsrTimings
from asr_metrics.collector import MetricsCollector


def test_metrics_collector_record() -> None:
    collector = MetricsCollector(pricing_per_minute={"mock": 0.0})
    response = AsrResponse(
        text="hello world",
        language="en-US",
        backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
        timings=AsrTimings(preprocess_ms=1.0, inference_ms=20.0, postprocess_ms=1.0),
        audio_duration_sec=1.0,
        success=True,
    )
    rec = collector.record(
        backend="mock",
        scenario="clean",
        wav_path="data/sample/vosk_test.wav",
        language="en-US",
        reference_text="hello world",
        response=response,
    )
    assert rec.wer == 0.0
    assert rec.cer == 0.0
    assert rec.latency_ms == 22.0
    assert rec.rtf > 0.0


def test_metrics_collector_estimate_cost_uses_base_backend() -> None:
    collector = MetricsCollector(pricing_per_minute={"whisper": 0.2})
    # 30 sec with 0.2/minute -> 0.1
    assert collector.estimate_cost("whisper:large-v3", 30.0) == 0.1


def test_metrics_collector_sets_rtf_zero_for_zero_duration() -> None:
    collector = MetricsCollector(pricing_per_minute={"mock": 0.0})
    response = AsrResponse(
        text="",
        language="en-US",
        backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
        timings=AsrTimings(preprocess_ms=1.0, inference_ms=10.0, postprocess_ms=1.0),
        audio_duration_sec=0.0,
        success=False,
    )
    rec = collector.record(
        backend="mock",
        scenario="clean",
        wav_path="data/sample/vosk_test.wav",
        language="en-US",
        reference_text="",
        response=response,
    )
    assert rec.rtf == 0.0
