"""Secrets reference loading and secure resolution utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from asr_config.models import SecretRef


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Secret ref file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Secret ref root must be an object: {path}")
    return data


def load_secret_ref(path: str) -> SecretRef:
    """Load secret reference definition from YAML file."""
    source_path = Path(path)
    raw = _load_yaml(source_path)
    return SecretRef(
        ref_id=str(raw.get("ref_id", "")),
        provider=str(raw.get("provider", "")),
        kind=str(raw.get("kind", "none")),
        path=str(raw.get("path", "")),
        env_fallback=str(raw.get("env_fallback", "")),
        required=[str(x) for x in raw.get("required", [])],
        optional=[str(x) for x in raw.get("optional", [])],
        masked=bool(raw.get("masked", True)),
        source_path=str(source_path),
    )


def resolve_secret_ref(ref: SecretRef) -> dict[str, str]:
    """Resolve secret reference using env/file model.

    Returns a dictionary intended for provider initialization.
    """
    if ref.kind == "none":
        return {}

    result: dict[str, str] = {}

    if ref.kind == "file":
        if ref.path:
            candidate = Path(ref.path).expanduser()
            if not candidate.is_absolute():
                source_root = Path(ref.source_path).resolve().parent if ref.source_path else Path.cwd()
                project_root = source_root.parent.parent if source_root.name == "refs" else source_root
                relative_to_project = project_root / candidate
                relative_to_ref_dir = source_root / candidate
                if relative_to_project.exists():
                    candidate = relative_to_project
                else:
                    candidate = relative_to_ref_dir
            result["file_path"] = str(candidate)
        if ref.env_fallback:
            env_value = os.getenv(ref.env_fallback, "").strip()
            if env_value:
                result["file_path"] = env_value
        file_path = result.get("file_path", "")
        if file_path and not Path(file_path).exists():
            raise FileNotFoundError(f"Secret file does not exist: {file_path}")

    if ref.kind in {"env", "file"}:
        for key in ref.required:
            value = os.getenv(key, "").strip()
            if not value:
                raise ValueError(f"Required secret env is missing: {key}")
            result[key] = value
        for key in ref.optional:
            value = os.getenv(key, "").strip()
            if value:
                result[key] = value

    return result


def mask_secret_values(values: dict[str, str]) -> dict[str, str]:
    """Mask secret values before logging."""
    masked: dict[str, str] = {}
    for key, value in values.items():
        if not value:
            masked[key] = ""
            continue
        if len(value) <= 6:
            masked[key] = "***"
            continue
        masked[key] = f"{value[:2]}***{value[-2:]}"
    return masked
