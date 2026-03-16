from __future__ import annotations

import wave
from pathlib import Path

from asr_benchmark_core.noise import apply_noise_to_wav, resolve_noise_plan


def _read_frames(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.readframes(wav_file.getnframes())


def test_resolve_noise_plan_returns_configured_levels() -> None:
    plan = resolve_noise_plan(
        scenario="noise_robustness",
        benchmark_settings={"noise": {"mode": "white", "levels": ["clean", "light", "heavy"]}},
    )

    assert [item["noise_level"] for item in plan] == ["clean", "light", "heavy"]
    assert plan[0]["snr_db"] is None
    assert plan[1]["snr_db"] == 30
    assert plan[2]["snr_db"] == 10


def test_apply_noise_to_wav_creates_distinct_variant(sample_wav: str, tmp_path: Path) -> None:
    source = Path(sample_wav)
    noisy = tmp_path / "noisy.wav"

    output_path = apply_noise_to_wav(
        source_path=str(source),
        output_path=str(noisy),
        snr_db=20.0,
        seed=42,
    )

    assert noisy.exists()
    assert output_path == str(noisy)
    assert _read_frames(source) != _read_frames(noisy)
