from __future__ import annotations

import json
from pathlib import Path

import pytest
from asr_datasets.manifest import DatasetSample, load_manifest, save_manifest, validate_sample


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
