from __future__ import annotations

import json
from pathlib import Path

import pytest
from asr_datasets.importer import import_from_uploaded_files


def test_import_from_uploaded_files_rejects_duplicate_normalized_filenames(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate filenames"):
        import_from_uploaded_files(
            files=[
                {"name": "nested/a.wav", "content": b"one"},
                {"name": "other/a.wav", "content": b"two"},
                {"name": "nested/a.txt", "content": b"hello"},
            ],
            target_dataset_id="dup_upload",
            imported_root=str(tmp_path / "imported"),
            manifests_root=str(tmp_path / "manifests"),
        )


def test_import_from_uploaded_files_rejects_manifest_missing_uploaded_audio(tmp_path: Path) -> None:
    manifest_payload = {
        "sample_id": "sample_001",
        "audio_path": "missing.wav",
        "transcript": "hello",
        "language": "en-US",
    }

    with pytest.raises(ValueError, match="not included in the upload bundle"):
        import_from_uploaded_files(
            files=[
                {
                    "name": "dataset.jsonl",
                    "content": (json.dumps(manifest_payload) + "\n").encode("utf-8"),
                },
                {"name": "other.wav", "content": b"RIFF0000WAVE"},
            ],
            target_dataset_id="manifest_missing_audio",
            imported_root=str(tmp_path / "imported"),
            manifests_root=str(tmp_path / "manifests"),
        )


def test_import_from_uploaded_files_rewrites_manifest_audio_to_saved_bundle_paths(
    tmp_path: Path,
) -> None:
    manifest_payload = {
        "sample_id": "sample_001",
        "audio_path": "audio.wav",
        "transcript": "hello",
        "language": "en-US",
    }

    manifest_path, sample_count = import_from_uploaded_files(
        files=[
            {
                "name": "dataset.jsonl",
                "content": (json.dumps(manifest_payload) + "\n").encode("utf-8"),
            },
            {"name": "audio.wav", "content": b"RIFF0000WAVE"},
        ],
        target_dataset_id="manifest_bundle",
        imported_root=str(tmp_path / "imported"),
        manifests_root=str(tmp_path / "manifests"),
    )

    assert sample_count == 1
    payload = json.loads(Path(manifest_path).read_text(encoding="utf-8").strip())
    assert Path(payload["audio_path"]).exists()
    assert payload["audio_path"].endswith("audio.wav")
