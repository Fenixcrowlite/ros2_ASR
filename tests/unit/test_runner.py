import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from asr_benchmark.dataset import DatasetItem
from asr_benchmark.runner import (
    _backend_supports_streaming,
    _normalize_scenarios,
    _run_streaming_sim,
    run_benchmark,
)
from asr_core.models import AsrResponse, AsrTimings
from asr_metrics.collector import MetricsCollector

pytestmark = pytest.mark.legacy


def _write_test_wav(path: Path, *, sample_rate: int, frames: int) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)


class _StreamingProbeBackend:
    def __init__(self) -> None:
        self.last_sample_rate: int | None = None
        self.capabilities = SimpleNamespace(supports_streaming=True)

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


def test_backend_supports_streaming_checks_capabilities_flag() -> None:
    assert _backend_supports_streaming(
        SimpleNamespace(capabilities=SimpleNamespace(supports_streaming=True))
    ) is True
    assert _backend_supports_streaming(
        SimpleNamespace(capabilities=SimpleNamespace(supports_streaming=False))
    ) is False
    assert _backend_supports_streaming(SimpleNamespace()) is False


def test_run_benchmark_skips_streaming_records_for_batch_only_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asr_benchmark.runner as runner_module

    class _BatchOnlyBackend:
        capabilities = SimpleNamespace(supports_streaming=False)

        def recognize_once(self, request) -> AsrResponse:
            del request
            return AsrResponse(
                text="batch only result",
                language="en-US",
                backend_info={"provider": "batch_only", "model": "probe", "region": "local"},
                timings=AsrTimings(preprocess_ms=1.0, inference_ms=2.0, postprocess_ms=1.0),
                audio_duration_sec=1.0,
                success=True,
            )

    monkeypatch.setattr(runner_module, "create_backend", lambda backend_name, config=None: _BatchOnlyBackend())
    monkeypatch.setattr(runner_module, "generate_all_plots", lambda records, out_dir: None)

    records = run_benchmark(
        config_path="configs/default.yaml",
        dataset_path="data/transcripts/sample_manifest.csv",
        output_json=str(tmp_path / "bench.json"),
        output_csv=str(tmp_path / "bench.csv"),
        backends=["batch_only"],
    )

    assert records
    assert all(record.scenario != "streaming_sim" for record in records)


def test_normalize_scenarios_accepts_comma_separated_string() -> None:
    scenarios = _normalize_scenarios("clean,snr20,snr10")
    assert scenarios == ["clean", "snr20", "snr10"]


def test_normalize_scenarios_rejects_invalid_type() -> None:
    with pytest.raises(ValueError, match="list or comma-separated string"):
        _normalize_scenarios({"clean": True})


def test_normalize_scenarios_rejects_unsupported_label() -> None:
    with pytest.raises(ValueError, match="Unsupported scenario"):
        _normalize_scenarios(["clean", "noise"])


def test_run_benchmark_accepts_comma_separated_scenarios_in_config(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "asr:",
                "  backend: mock",
                "backends:",
                "  mock:",
                "    deterministic_latency_ms: 1",
                "benchmark:",
                "  scenarios: clean,snr20",
                "  chunk_sec: 0.8",
                "  pricing:",
                "    mock: 0.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_json = tmp_path / "bench.json"
    out_csv = tmp_path / "bench.csv"

    records = run_benchmark(
        config_path=str(cfg),
        dataset_path="data/transcripts/sample_manifest.csv",
        output_json=str(out_json),
        output_csv=str(out_csv),
        backends=["mock"],
    )

    assert records
    assert any(record.scenario == "snr20" for record in records)


def test_run_benchmark_rejects_invalid_scenario_in_config(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "asr:",
                "  backend: mock",
                "backends:",
                "  mock:",
                "    deterministic_latency_ms: 1",
                "benchmark:",
                "  scenarios:",
                "    - clean",
                "    - noise",
                "  chunk_sec: 0.8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported scenario"):
        run_benchmark(
            config_path=str(cfg),
            dataset_path="data/transcripts/sample_manifest.csv",
            output_json=str(tmp_path / "bench.json"),
            output_csv=str(tmp_path / "bench.csv"),
            backends=["mock"],
        )
