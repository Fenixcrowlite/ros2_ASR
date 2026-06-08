"""Minimal configuration helpers used by canonical providers."""

from __future__ import annotations

import os
import re
from typing import Any

_ENV_PLACEHOLDER_RE = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def env_or(config: dict[str, Any], key: str, env_name: str, default: str = "") -> str:
    """Read string from ENV first, then from config key, then default."""
    value = os.getenv(env_name)
    if value:
        return value
    config_value = str(config.get(key, default))
    match = _ENV_PLACEHOLDER_RE.match(config_value.strip())
    if match:
        return os.getenv(match.group(1), "")
    return config_value


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
