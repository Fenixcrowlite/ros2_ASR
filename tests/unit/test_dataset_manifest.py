from __future__ import annotations

import json
from pathlib import Path

import pytest
from asr_datasets.manifest import (
    DatasetSample,
    _resolve_audio_path,
    load_manifest,
    save_manifest,
    validate_sample,
)


def test_validate_sample_requires_core_fields() -> None:
    sample = DatasetSample(sample_id="", audio_path="", transcript="", language="")
    errors = validate_sample(sample)
    assert "sample_id is required" in errors
    assert "audio_path is required" in errors
    assert "transcript is required" in errors
    assert "language is required" in errors


def test_load_manifest_reads_valid_fixture(repo_root: Path) -> None:
    manifest_path = repo_root / "tests" / "fixtures" / "manifests" / "valid_dataset.jsonl"
    samples = load_manifest(str(manifest_path))

    assert len(samples) == 2
    assert samples[0].sample_id == "sample_001"
    assert samples[1].language == "en-US"


def test_repo_sample_dataset_manifest_resolves_to_real_audio(repo_root: Path) -> None:
    manifest_path = repo_root / "datasets" / "manifests" / "sample_dataset.jsonl"

    samples = load_manifest(str(manifest_path))

    assert len(samples) == 1
    assert Path(samples[0].audio_path).exists()
    assert Path(samples[0].audio_path).resolve() == (
        repo_root / "data" / "sample" / "vosk_test.wav"
    ).resolve()


def test_load_manifest_resolves_relative_audio_paths_from_manifest_directory(
    tmp_path: Path,
) -> None:
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    wav_path = audio_dir / "sample.wav"
    wav_path.write_bytes(b"RIFF0000WAVE")
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "sample_id": "sample_rel",
                "audio_path": "audio/sample.wav",
                "transcript": "hello",
                "language": "en-US",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    samples = load_manifest(str(manifest_path))

    assert len(samples) == 1
    assert Path(samples[0].audio_path).resolve() == wav_path.resolve()


def test_resolve_audio_path_is_deterministic_regardless_of_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_dir = tmp_path / "dataset"
    manifest_dir.mkdir()
    manifest_path = manifest_dir / "manifest.jsonl"
    cwd_dir = tmp_path / "elsewhere"
    cwd_audio = cwd_dir / "audio"
    cwd_audio.mkdir(parents=True)
    (cwd_audio / "sample.wav").write_bytes(b"RIFF0000WAVE")
    expected = str((manifest_dir / "audio" / "sample.wav").resolve())

    monkeypatch.chdir(cwd_dir)
    resolved_from_elsewhere = _resolve_audio_path(manifest_path, "audio/sample.wav")
    monkeypatch.chdir(tmp_path)
    resolved_from_tmp_root = _resolve_audio_path(manifest_path, "audio/sample.wav")

    assert resolved_from_elsewhere == expected
    assert resolved_from_tmp_root == expected


def test_load_manifest_rejects_duplicate_sample_ids(repo_root: Path) -> None:
    manifest_path = repo_root / "tests" / "fixtures" / "manifests" / "duplicate_sample_ids.jsonl"
    with pytest.raises(ValueError, match="duplicate sample_id"):
        load_manifest(str(manifest_path))


def test_save_manifest_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "roundtrip.jsonl"
    samples = [
        DatasetSample(
            sample_id="sample_1",
            audio_path="data/sample/vosk_test.wav",
            transcript="hello world",
            language="en-US",
            metadata={"split_source": "generated"},
        )
    ]

    save_manifest(str(target), samples)

    payload = json.loads(target.read_text(encoding="utf-8").strip())
    assert payload["sample_id"] == "sample_1"
    assert payload["metadata"]["split_source"] == "generated"
