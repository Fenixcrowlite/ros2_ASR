"""Dataset manifest loader for benchmark experiments."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DatasetItem:
    """One benchmark sample entry from manifest CSV."""

    wav_path: str
    transcript: str
    language: str
    resolved_wav_path: str = ""


def load_manifest_csv(path: str) -> list[DatasetItem]:
    """Load dataset manifest with columns: `wav_path, transcript, language`."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")

    items: list[DatasetItem] = []
    with manifest_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"wav_path", "transcript"}
        columns = set(reader.fieldnames or [])
        missing_columns = sorted(required - columns)
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(f"Dataset manifest is missing required columns: {missing}")

        for row_index, row in enumerate(reader, start=2):
            raw_wav_path = str(row.get("wav_path") or "").strip()
            transcript = str(row.get("transcript") or "").strip()
            if not raw_wav_path and not transcript:
                continue
            if not raw_wav_path:
                raise ValueError(f"Dataset row {row_index}: wav_path is required")
            if not transcript:
                raise ValueError(f"Dataset row {row_index}: transcript is required")

            wav_candidate = Path(raw_wav_path).expanduser()
            if wav_candidate.is_absolute():
                resolved_wav = wav_candidate.resolve()
            else:
                from_manifest = (manifest_path.parent / wav_candidate).resolve()
                from_cwd = (Path.cwd() / wav_candidate).resolve()
                # Prefer paths relative to manifest location for reproducible runs.
                if from_manifest.exists():
                    resolved_wav = from_manifest
                elif from_cwd.exists():
                    resolved_wav = from_cwd
                else:
                    raise ValueError(
                        "Dataset row "
                        f"{row_index}: wav_path does not exist from current directory "
                        f"or manifest directory: {raw_wav_path}"
                    )

            if not resolved_wav.exists():
                raise ValueError(
                    f"Dataset row {row_index}: wav_path does not exist: {resolved_wav}"
                )
            if resolved_wav.suffix.lower() != ".wav":
                raise ValueError(f"Dataset row {row_index}: wav_path must point to .wav file")

            items.append(
                DatasetItem(
                    wav_path=raw_wav_path,
                    transcript=transcript,
                    language=str(row.get("language") or "en-US").strip() or "en-US",
                    resolved_wav_path=str(resolved_wav),
                )
            )
    return items
