"""Profile persistence for Web GUI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from web_gui.app.paths import PROFILES_DIR

_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_name(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip())
    slug = slug.strip("-._")
    return slug or "profile"


def profile_path(name: str) -> Path:
    """Get absolute profile path for provided logical name."""
    safe = _safe_name(name)
    return PROFILES_DIR / f"{safe}.yaml"


def save_profile(name: str, payload: dict[str, Any]) -> Path:
    """Save profile YAML payload and return destination path."""
    path = profile_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=False)
    return path


def load_profile(name: str) -> dict[str, Any]:
    """Load profile payload."""
    path = profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    with path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid profile payload in {path}")
    return payload
