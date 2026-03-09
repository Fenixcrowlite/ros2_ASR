import wave
from pathlib import Path

import pytest
from asr_benchmark.dataset import DatasetItem
from asr_benchmark.runner import _run_streaming_sim, run_benchmark
from asr_core.models import AsrResponse, AsrTimings
from asr_metrics.collector import MetricsCollector


def _write_test_wav(path: Path, *, sample_rate: int, frames: int) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)


class _StreamingProbeBackend:
    def __init__(self) -> None:
        self.last_sample_rate: int | None = None

    def streaming_recognize(
        self,
        _chunks: list[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        self.last_sample_rate = sample_rate
        return AsrResponse(
            text="probe result",
            language=language,
            backend_info={"provider": "probe", "model": "probe", "region": "local"},
            timings=AsrTimings(preprocess_ms=1.0, inference_ms=2.0, postprocess_ms=1.0),
            audio_duration_sec=1.0,
            success=True,
        )


def test_run_benchmark_mock(tmp_path: Path) -> None:
    out_json = tmp_path / "bench.json"
    out_csv = tmp_path / "bench.csv"
    records = run_benchmark(
        config_path="configs/default.yaml",
        dataset_path="data/transcripts/sample_manifest.csv",
        output_json=str(out_json),
        output_csv=str(out_csv),
        backends=["mock"],
    )
    assert records
    assert out_json.exists()
    assert out_csv.exists()
    assert (tmp_path / "plots" / "wer_by_backend.png").exists()


def test_run_benchmark_rejects_empty_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "empty_manifest.csv"
    manifest.write_text("wav_path,transcript,language\n", encoding="utf-8")
    out_json = tmp_path / "bench.json"
    out_csv = tmp_path / "bench.csv"

    with pytest.raises(ValueError, match="empty"):
        run_benchmark(
            config_path="configs/default.yaml",
            dataset_path=str(manifest),
            output_json=str(out_json),
            output_csv=str(out_csv),
            backends=["mock"],
        )


def test_streaming_sim_uses_actual_wav_sample_rate(tmp_path: Path) -> None:
    wav_path = tmp_path / "sample_8k.wav"
    _write_test_wav(wav_path, sample_rate=8000, frames=8000)

    item = DatasetItem(
        wav_path="sample_8k.wav",
        resolved_wav_path=str(wav_path),
        transcript="probe result",
        language="en-US",
    )
    backend = _StreamingProbeBackend()
    collector = MetricsCollector(pricing_per_minute={"probe": 0.0})

    record = _run_streaming_sim(
        backend,
        "probe",
        item,
        0.2,
        collector,
    )

    assert backend.last_sample_rate == 8000
    assert record.success
