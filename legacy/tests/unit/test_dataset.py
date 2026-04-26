from __future__ import annotations

import wave
from pathlib import Path

import pytest
from asr_benchmark.dataset import load_manifest_csv

pytestmark = pytest.mark.legacy


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


def test_manifest_resolution_prefers_manifest_directory_over_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_dir = tmp_path / "manifest_dir"
    manifest_dir.mkdir()
    manifest_wav = manifest_dir / "sample.wav"
    _write_test_wav(manifest_wav)

    cwd_dir = tmp_path / "cwd_dir"
    cwd_dir.mkdir()
    cwd_wav = cwd_dir / "sample.wav"
    _write_test_wav(cwd_wav)
    monkeypatch.chdir(cwd_dir)

    manifest = manifest_dir / "manifest.csv"
    manifest.write_text(
        "wav_path,transcript,language\nsample.wav,hello world,en-US\n",
        encoding="utf-8",
    )

    items = load_manifest_csv(str(manifest))

    assert len(items) == 1
    assert Path(items[0].resolved_wav_path).resolve() == manifest_wav.resolve()


def test_manifest_rejects_cwd_only_relative_audio(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_dir = tmp_path / "manifest_dir"
    manifest_dir.mkdir()

    cwd_dir = tmp_path / "cwd_dir"
    cwd_dir.mkdir()
    cwd_wav = cwd_dir / "sample.wav"
    _write_test_wav(cwd_wav)
    monkeypatch.chdir(cwd_dir)

    manifest = manifest_dir / "manifest.csv"
    manifest.write_text(
        "wav_path,transcript,language\nsample.wav,hello world,en-US\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="relative to manifest directory"):
        load_manifest_csv(str(manifest))


def test_manifest_resolves_project_root_relative_audio(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    (project_root / ".git").mkdir(parents=True)
    (project_root / "data" / "sample").mkdir(parents=True)
    (project_root / "data" / "transcripts").mkdir(parents=True)
    (project_root / "configs").mkdir(parents=True)

    wav_path = project_root / "data" / "sample" / "sample.wav"
    _write_test_wav(wav_path)
    manifest = project_root / "data" / "transcripts" / "manifest.csv"
    manifest.write_text(
        "wav_path,transcript,language\ndata/sample/sample.wav,hello world,en-US\n",
        encoding="utf-8",
    )

    items = load_manifest_csv(str(manifest))

    assert len(items) == 1
    assert Path(items[0].resolved_wav_path).resolve() == wav_path.resolve()
