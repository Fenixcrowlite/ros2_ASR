"""Storage metadata models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ArtifactRef:
    """Reference to an artifact persisted on disk."""

    run_id: str
    artifact_type: str
    path: str
    checksum: str = ""
    size_bytes: int = 0
