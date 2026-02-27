"""Dataset manifest loader for benchmark experiments."""

from __future__ import annotations

import csv
from dataclasses import dataclass


@dataclass(slots=True)
class DatasetItem:
    """One benchmark sample entry from manifest CSV."""

    wav_path: str
    transcript: str
    language: str


def load_manifest_csv(path: str) -> list[DatasetItem]:
    """Load dataset manifest with columns: `wav_path, transcript, language`."""
    items: list[DatasetItem] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(
                DatasetItem(
                    wav_path=row["wav_path"],
                    transcript=row["transcript"],
                    language=row.get("language", "en-US"),
                )
            )
    return items
