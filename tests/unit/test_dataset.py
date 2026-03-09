from __future__ import annotations

import wave
from pathlib import Path

import pytest
from asr_benchmark.dataset import load_manifest_csv


def _write_test_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 1600)


def test_manifest_requires_wav_and_transcript_columns(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("wav_path,language\nsample.wav,en-US\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_manifest_csv(str(manifest))


def test_manifest_resolves_relative_wav_from_manifest_directory(tmp_path: Path) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "wav_path,transcript,language\nsample.wav,hello world,en-US\n",
        encoding="utf-8",
    )

    items = load_manifest_csv(str(manifest))

    assert len(items) == 1
    assert items[0].wav_path == "sample.wav"
    assert Path(items[0].resolved_wav_path).resolve() == wav_path.resolve()
