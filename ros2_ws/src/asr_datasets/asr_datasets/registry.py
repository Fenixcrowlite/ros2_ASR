"""Dataset registry utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DatasetEntry:
    dataset_id: str
    manifest_ref: str
    sample_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetRegistry:
    def __init__(self, registry_path: str = "datasets/registry/datasets.json") -> None:
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self.registry_path.write_text('{"datasets": []}\n', encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Dataset registry root must be object")
        payload.setdefault("datasets", [])
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.registry_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def list(self) -> list[DatasetEntry]:
        payload = self._load()
        entries: list[DatasetEntry] = []
        for item in payload.get("datasets", []):
            entries.append(
                DatasetEntry(
                    dataset_id=str(item.get("dataset_id", "")),
                    manifest_ref=str(item.get("manifest_ref", "")),
                    sample_count=int(item.get("sample_count", 0) or 0),
                    metadata=dict(item.get("metadata", {})),
                )
            )
        return entries

    def register(self, entry: DatasetEntry) -> None:
        payload = self._load()
        datasets = [
            item
            for item in payload.get("datasets", [])
            if item.get("dataset_id") != entry.dataset_id
        ]
        datasets.append(asdict(entry))
        payload["datasets"] = datasets
        self._save(payload)
