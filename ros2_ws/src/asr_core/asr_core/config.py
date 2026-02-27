from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def _deep_update(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_yaml(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def load_runtime_config(
    default_config_path: str, commercial_config_path: str | None = None
) -> dict[str, Any]:
    cfg = load_yaml(default_config_path)
    if commercial_config_path:
        cfg = _deep_update(cfg, load_yaml(commercial_config_path))
    commercial_local = Path("configs/commercial.yaml")
    if commercial_local.exists():
        cfg = _deep_update(cfg, load_yaml(str(commercial_local)))
    return cfg


def env_or(config: dict[str, Any], key: str, env_name: str, default: str = "") -> str:
    value = os.getenv(env_name)
    if value:
        return value
    return str(config.get(key, default))


def as_bool(value: Any, default: bool = False) -> bool:
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
