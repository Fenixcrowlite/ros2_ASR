"""Dataset manifest model and validation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from json import JSONDecodeError
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DatasetSample:
    sample_id: str
    audio_path: str
    transcript: str
    language: str
    duration_sec: float = 0.0
    split: str = "test"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


REQUIRED_FIELDS = {"sample_id", "audio_path", "transcript", "language"}


def validate_sample(sample: DatasetSample) -> list[str]:
    errors: list[str] = []
    if not sample.sample_id:
        errors.append("sample_id is required")
    if not sample.audio_path:
        errors.append("audio_path is required")
    if not sample.transcript:
        errors.append("transcript is required")
    if not sample.language:
        errors.append("language is required")
    return errors


def load_manifest(path: str) -> list[DatasetSample]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")

    samples: list[DatasetSample] = []
    seen_ids: set[str] = set()
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except JSONDecodeError as exc:
                raise ValueError(f"Manifest line {line_no}: invalid JSON: {exc.msg}") from exc
            missing = REQUIRED_FIELDS - set(payload.keys())
            if missing:
                raise ValueError(f"Manifest line {line_no}: missing fields: {sorted(missing)}")
            sample = DatasetSample(
                sample_id=str(payload.get("sample_id", "")),
                audio_path=str(payload.get("audio_path", "")),
                transcript=str(payload.get("transcript", "")),
                language=str(payload.get("language", "")),
                duration_sec=float(payload.get("duration_sec", 0.0) or 0.0),
                split=str(payload.get("split", "test")),
                tags=[str(item) for item in payload.get("tags", [])],
                metadata=dict(payload.get("metadata", {})),
            )
            errors = validate_sample(sample)
            if errors:
                raise ValueError(f"Manifest line {line_no}: {'; '.join(errors)}")
            if sample.sample_id in seen_ids:
                raise ValueError(f"Manifest line {line_no}: duplicate sample_id: {sample.sample_id}")
            seen_ids.add(sample.sample_id)
            samples.append(sample)
    return samples


def save_manifest(path: str, samples: list[DatasetSample]) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(asdict(sample), ensure_ascii=True) + "\n")
