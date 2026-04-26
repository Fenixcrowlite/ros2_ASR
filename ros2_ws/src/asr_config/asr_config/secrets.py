"""Secrets reference loading and secure resolution utilities."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from asr_config.models import SecretRef

ENV_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def _is_azure_endpoint_url(value: str) -> bool:
    text = str(value or "").strip().lower()
    return text.startswith(("https://", "http://", "wss://"))


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


def _project_root_from_source(source_path: str) -> Path:
    source = Path(source_path).expanduser() if source_path else Path.cwd()
    source_root = source.resolve().parent if source_path else Path.cwd()
    if source_root.name == "refs" and source_root.parent.name == "secrets":
        return source_root.parent.parent
    return source_root


def local_env_file_path(source_path: str = "") -> Path:
    """Return the local `.env`-style file used for runtime secret injection."""
    env_path = os.getenv("ASR_LOCAL_ENV_FILE", "").strip()
    if env_path:
        return Path(env_path).expanduser()
    project_root = _project_root_from_source(source_path)
    return project_root / "secrets" / "local" / "runtime.env"


def load_local_env_values(source_path: str = "") -> dict[str, str]:
    """Load key/value pairs from the local runtime env file when it exists."""
    path = local_env_file_path(source_path)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def resolve_env_value(key: str, source_path: str = "") -> tuple[str, str]:
    """Resolve a secret from process env first and local env file second."""
    process_value = os.getenv(key, "").strip()
    if process_value:
        return process_value, "process_env"
    local_values = load_local_env_values(source_path)
    local_value = str(local_values.get(key, "")).strip()
    if local_value:
        return local_value, "local_env_file"
    return "", ""


def write_local_env_values(
    updates: dict[str, str],
    *,
    source_path: str = "",
    unset: Iterable[str] = (),
) -> Path:
    """Update the local runtime env file and return its path."""
    path = local_env_file_path(source_path)
    current = load_local_env_values(source_path)
    for key in unset:
        current.pop(str(key), None)
    for key, value in updates.items():
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        if not ENV_KEY_RE.match(normalized_key):
            raise ValueError(f"Invalid env key: {normalized_key}")
        normalized_value = str(value)
        if any(char in normalized_value for char in ("\r", "\n", "\0")):
            raise ValueError(
                f"Invalid env value for {normalized_key}: control characters are not allowed"
            )
        if normalized_value:
            current[normalized_key] = normalized_value
        else:
            current.pop(normalized_key, None)

    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# Local runtime env injection for native provider auth.",
        "# This file is ignored by git. Use native env var names only.",
    ]
    body = [f"{key}={current[key]}" for key in sorted(current)]
    path.write_text("\n".join(header + body) + ("\n" if body else "\n"), encoding="utf-8")
    return path


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
            env_value, _ = resolve_env_value(ref.env_fallback, ref.source_path)
            if env_value:
                result["file_path"] = env_value
        file_path = result.get("file_path", "")
        if file_path and not Path(file_path).exists():
            raise FileNotFoundError(f"Secret file does not exist: {file_path}")

    if ref.kind in {"env", "file"}:
        azure_endpoint_value = ""
        azure_endpoint_url = False
        if ref.provider == "azure" and ref.kind == "env":
            azure_endpoint_value, _ = resolve_env_value("ASR_AZURE_ENDPOINT", ref.source_path)
            azure_endpoint_url = _is_azure_endpoint_url(azure_endpoint_value)

        for key in ref.required:
            if (
                ref.provider == "azure"
                and ref.kind == "env"
                and key == "AZURE_SPEECH_REGION"
                and azure_endpoint_url
            ):
                value, _ = resolve_env_value(key, ref.source_path)
                if value:
                    result[key] = value
                continue
            value, _ = resolve_env_value(key, ref.source_path)
            if not value:
                raise ValueError(f"Required secret env is missing: {key}")
            result[key] = value
        for key in ref.optional:
            value, _ = resolve_env_value(key, ref.source_path)
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
