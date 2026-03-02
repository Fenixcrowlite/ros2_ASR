"""Runtime config construction helpers for Web GUI."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from web_gui.app.paths import REPO_ROOT, RUNTIME_CONFIGS_DIR

_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class ConfigBuildError(RuntimeError):
    """Raised when runtime config cannot be built."""


def _safe_slug(raw: str) -> str:
    value = _SLUG_RE.sub("-", raw.strip())
    value = value.strip("-._")
    return value or "run"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigBuildError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    if not isinstance(payload, dict):
        raise ConfigBuildError(f"Config payload must be mapping: {path}")
    return payload


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two mapping objects and return new object."""
    result: dict[str, Any] = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _ensure_backend(runtime_cfg: dict[str, Any], backend: str) -> dict[str, Any]:
    runtime_cfg.setdefault("backends", {})
    if not isinstance(runtime_cfg["backends"], dict):
        runtime_cfg["backends"] = {}
    runtime_cfg["backends"].setdefault(backend, {})
    if not isinstance(runtime_cfg["backends"][backend], dict):
        runtime_cfg["backends"][backend] = {}
    return runtime_cfg["backends"][backend]


def _apply_secrets(runtime_cfg: dict[str, Any], secrets: dict[str, str]) -> None:
    """Inject secrets into runtime config payload."""
    if not secrets:
        return

    google_cfg = _ensure_backend(runtime_cfg, "google")
    aws_cfg = _ensure_backend(runtime_cfg, "aws")
    azure_cfg = _ensure_backend(runtime_cfg, "azure")

    if secrets.get("google_credentials_json"):
        google_cfg["credentials_json"] = secrets["google_credentials_json"]
    if secrets.get("google_project_id"):
        google_cfg["project_id"] = secrets["google_project_id"]
    if secrets.get("google_region"):
        google_cfg["region"] = secrets["google_region"]

    if secrets.get("aws_access_key_id"):
        aws_cfg["access_key_id"] = secrets["aws_access_key_id"]
    if secrets.get("aws_secret_access_key"):
        aws_cfg["secret_access_key"] = secrets["aws_secret_access_key"]
    if secrets.get("aws_session_token"):
        aws_cfg["session_token"] = secrets["aws_session_token"]
    if secrets.get("aws_region"):
        aws_cfg["region"] = secrets["aws_region"]
    if secrets.get("aws_s3_bucket"):
        aws_cfg["s3_bucket"] = secrets["aws_s3_bucket"]

    if secrets.get("azure_speech_key"):
        azure_cfg["speech_key"] = secrets["azure_speech_key"]
    if secrets.get("azure_region"):
        azure_cfg["region"] = secrets["azure_region"]
    if secrets.get("azure_endpoint"):
        azure_cfg["endpoint"] = secrets["azure_endpoint"]


def _extract_env_secrets(secrets: dict[str, str]) -> dict[str, str]:
    """Extract env vars from provided secret dictionary."""
    mapping = {
        "google_credentials_json": "GOOGLE_APPLICATION_CREDENTIALS",
        "google_project_id": "GOOGLE_CLOUD_PROJECT",
        "aws_access_key_id": "AWS_ACCESS_KEY_ID",
        "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
        "aws_session_token": "AWS_SESSION_TOKEN",
        "aws_region": "AWS_REGION",
        "azure_speech_key": "AZURE_SPEECH_KEY",
        "azure_region": "AZURE_SPEECH_REGION",
    }
    env: dict[str, str] = {}
    for key, env_name in mapping.items():
        value = secrets.get(key, "")
        if value:
            env[env_name] = value
    return env


def build_runtime_config(
    *,
    base_config_path: str,
    runtime_overrides: dict[str, Any],
    secrets: dict[str, str] | None = None,
    profile_name: str = "",
) -> tuple[Path, dict[str, Any], dict[str, str]]:
    """Build and persist runtime config file for one GUI run."""
    base_path = (REPO_ROOT / base_config_path).resolve()
    base_cfg = _load_yaml(base_path)
    merged = deep_merge(base_cfg, runtime_overrides)
    cleaned_secrets = {k: str(v).strip() for k, v in (secrets or {}).items() if str(v).strip()}
    _apply_secrets(merged, cleaned_secrets)
    env_secrets = _extract_env_secrets(cleaned_secrets)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = _safe_slug(profile_name) if profile_name else "runtime"
    output_path = RUNTIME_CONFIGS_DIR / f"{timestamp}_{suffix}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(merged, fh, sort_keys=False, allow_unicode=False)

    return output_path, merged, env_secrets
