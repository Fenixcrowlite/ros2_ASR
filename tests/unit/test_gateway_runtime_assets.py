from __future__ import annotations

from pathlib import Path

import pytest
from asr_gateway.runtime_assets import (
    extract_wav_segment,
    list_runtime_samples,
    resolve_runtime_sample_path,
    runtime_upload_target,
    wav_metadata_from_bytes,
)
from fastapi import HTTPException


def _project_relative_factory(project_root: Path):
    def _project_relative(path: Path) -> str:
        return path.resolve().relative_to(project_root.resolve()).as_posix()

    return _project_relative


def test_list_runtime_samples_reports_valid_and_skipped_entries(
    sample_wav: str,
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    samples_root = project_root / "data" / "sample"
    uploads_root = samples_root / "uploads"
    samples_root.mkdir(parents=True)
    uploads_root.mkdir(parents=True)

    valid_wav = samples_root / "valid.wav"
    uploaded_wav = uploads_root / "uploaded.wav"
    bad_wav = samples_root / "broken.wav"
    ignored_file = samples_root / "notes.txt"

    valid_wav.write_bytes(Path(sample_wav).read_bytes())
    uploaded_wav.write_bytes(Path(sample_wav).read_bytes())
    bad_wav.write_bytes(b"not-a-wav")
    ignored_file.write_text("skip me", encoding="utf-8")

    payload = list_runtime_samples(
        samples_root=samples_root,
        uploads_root=uploads_root,
        project_relative_path=_project_relative_factory(project_root),
        sample_suffixes={".wav", ".wave"},
        upload_enabled=True,
    )

    assert payload["sample_count"] == 2
    assert payload["default_sample"] == "data/sample/valid.wav"
    assert any(item["path"] == "data/sample/valid.wav" for item in payload["samples"])
    assert any(item["path"] == "data/sample/uploads/uploaded.wav" for item in payload["samples"])
    assert any(item["path"] == "data/sample/broken.wav" for item in payload["skipped"])
    assert any(item["path"] == "data/sample/notes.txt" for item in payload["skipped"])


def test_runtime_upload_target_deduplicates_names(tmp_path: Path) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir()
    (uploads_root / "demo.wav").write_bytes(b"already-used")

    target = runtime_upload_target(
        "demo.wav",
        uploads_root=uploads_root,
        sample_suffixes={".wav", ".wave"},
    )

    assert target.name == "demo_1.wav"


def test_runtime_upload_target_rejects_non_wav(tmp_path: Path) -> None:
    with pytest.raises(HTTPException, match="supports WAV files only"):
        runtime_upload_target(
            "demo.mp3",
            uploads_root=tmp_path / "uploads",
            sample_suffixes={".wav", ".wave"},
        )


def test_resolve_runtime_sample_path_rejects_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    allowed_root = project_root / "data" / "sample"
    allowed_root.mkdir(parents=True)

    with pytest.raises(HTTPException, match="Unsafe sample_path"):
        resolve_runtime_sample_path(
            "../../etc/passwd",
            clean_name=lambda value, _label: value,
            project_root=project_root,
            allowed_roots=(allowed_root,),
        )


def test_wav_metadata_from_bytes_rejects_invalid_payload() -> None:
    with pytest.raises(ValueError, match="not a valid WAV file"):
        wav_metadata_from_bytes(b"bad-wav")


def test_extract_wav_segment_writes_requested_clip(sample_wav: str, tmp_path: Path) -> None:
    source = Path(sample_wav)
    output = tmp_path / "clip.wav"

    metadata = extract_wav_segment(
        source,
        output_path=output,
        start_sec=0.1,
        duration_sec=0.2,
    )

    assert output.exists()
    clipped = wav_metadata_from_bytes(output.read_bytes())
    assert clipped["duration_sec"] == pytest.approx(0.2, abs=0.03)
    assert metadata["start_sec"] == pytest.approx(0.1)
    assert metadata["duration_sec"] == pytest.approx(clipped["duration_sec"], abs=0.03)


def test_extract_wav_segment_rejects_start_beyond_end(sample_wav: str, tmp_path: Path) -> None:
    source = Path(sample_wav)
    output = tmp_path / "invalid_clip.wav"

    with pytest.raises(ValueError, match="start_sec exceeds source duration"):
        extract_wav_segment(
            source,
            output_path=output,
            start_sec=99.0,
            duration_sec=0.2,
        )
