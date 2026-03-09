from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from web_gui.app.validators import (
    validate_benchmark_request,
    validate_live_request,
    validate_ros_bringup_request,
)


def test_validate_live_language_rejects_invalid_code() -> None:
    with pytest.raises(HTTPException):
        validate_live_request({"language_mode": "manual", "language": "english"}, {})


def test_validate_live_accepts_valid_code() -> None:
    validate_live_request({"language_mode": "manual", "language": "en-US"}, {})


def test_validate_benchmark_dataset_missing_rejected() -> None:
    with pytest.raises(HTTPException):
        validate_benchmark_request({"dataset": "data/transcripts/not_found.csv"}, {})


def test_validate_ros_bringup_invalid_input_mode_rejected() -> None:
    with pytest.raises(HTTPException):
        validate_ros_bringup_request({"input_mode": "bad-mode"}, {})


def test_validate_benchmark_dataset_outside_allowed_roots_rejected(tmp_path: Path) -> None:
    dataset = tmp_path / "outside.csv"
    dataset.write_text("wav_path,transcript,language\n", encoding="utf-8")
    with pytest.raises(HTTPException):
        validate_benchmark_request({"dataset": str(dataset)}, {})


def test_validate_live_wav_outside_allowed_roots_rejected(tmp_path: Path) -> None:
    wav_path = tmp_path / "outside.wav"
    wav_path.write_bytes(b"RIFFxxxx")
    with pytest.raises(HTTPException):
        validate_live_request({"use_wav": str(wav_path)}, {})
