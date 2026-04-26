"""Minimal configuration helpers used by canonical providers."""

from __future__ import annotations

import os
from typing import Any


def env_or(config: dict[str, Any], key: str, env_name: str, default: str = "") -> str:
    """Read string from ENV first, then from config key, then default."""
    value = os.getenv(env_name)
    if value:
        return value
    return str(config.get(key, default))


def as_bool(value: Any, default: bool = False) -> bool:
    """Normalize common bool-like values from YAML/ENV/CLI."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default
