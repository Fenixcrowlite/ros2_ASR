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
        wav_path="data/sample/en_hello.wav",
        language="en-US",
        reference_text="hello world",
        response=response,
    )
    assert rec.wer == 0.0
    assert rec.cer == 0.0
    assert rec.latency_ms == 22.0
    assert rec.rtf > 0.0
