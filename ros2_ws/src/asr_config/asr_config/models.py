"""Configuration and secret reference models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SecretRef:
    """Reference to credentials without embedding raw secrets in profiles."""

    ref_id: str
    provider: str
    kind: str
    path: str = ""
    env_fallback: str = ""
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    masked: bool = True
    source_path: str = ""


@dataclass(slots=True)
class ResolvedConfig:
    """Resolved profile payload with provenance information."""

    profile_type: str
    profile_id: str
    data: dict[str, Any]
    merge_order: list[str] = field(default_factory=list)
    snapshot_path: str = ""
