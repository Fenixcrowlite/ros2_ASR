"""YAML-backed observability configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

DEFAULT_OBSERVABILITY_PROFILE = "default_observability"
DEFAULT_DEPLOYMENT_PROFILE = "dev_local"


@dataclass(slots=True)
class ObservabilityConfig:
    """Resolved metrics/trace export configuration loaded from YAML profiles."""

    profile_id: str = f"metrics/{DEFAULT_OBSERVABILITY_PROFILE}"
    artifact_root: str = "artifacts"
    reports_root: str = "reports"
    runtime_index_filename: str = "trace_index.csv"
    benchmark_index_filename: str = "trace_index.csv"
    export_json: bool = True
    export_csv: bool = True
    include_system_metrics: bool = True
    include_gpu_metrics: bool = True
    warn_only: bool = True
    require_ordered_timestamps: bool = True
    metric_names: list[str] = field(default_factory=list)


def _payload_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _payload_string(value: object, *, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _nested_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return data


def _profile_path(root: Path, profile_id: str) -> Path:
    filename = profile_id if profile_id.endswith(".yaml") else f"{profile_id}.yaml"
    return root / "metrics" / filename


def _resolve_profile_tree(root: Path, profile_id: str, visited: set[str]) -> dict[str, Any]:
    marker = str(profile_id).strip()
    if marker in visited:
        raise ValueError(f"Circular metrics profile inheritance detected: {marker}")
    visited.add(marker)

    payload = _load_yaml(_profile_path(root, marker))
    merged: dict[str, Any] = {}
    inherits = payload.get("inherits", [])
    if isinstance(inherits, str):
        inherits = [inherits]
    if not isinstance(inherits, list):
        raise ValueError(f"metrics inherits must be a list or string: {marker}")

    for inherited in inherits:
        inherited_id = str(inherited or "").strip()
        if not inherited_id:
            continue
        merged = _deep_merge(merged, _resolve_profile_tree(root, inherited_id, visited))
    return _deep_merge(merged, payload)


def load_observability_config(
    *,
    configs_root: str = "configs",
    profile_id: str | None = None,
    deployment_profile: str = DEFAULT_DEPLOYMENT_PROFILE,
) -> ObservabilityConfig:
    """Load and merge observability configuration from base, deployment, and profile YAML."""
    requested = str(
        profile_id or os.getenv("ASR_METRICS_PROFILE") or DEFAULT_OBSERVABILITY_PROFILE
    ).strip()
    normalized_profile = (
        requested.split("/", 1)[1] if requested.startswith("metrics/") else requested
    )
    root = Path(configs_root)
    payload = _deep_merge(
        _load_yaml(root / "metrics" / "_base.yaml"),
        _nested_mapping(
            _load_yaml(root / "deployment" / f"{deployment_profile}.yaml").get("metric_defaults", {})
        ),
    )
    payload = _deep_merge(payload, _resolve_profile_tree(root, normalized_profile, set()))
    exporters = _nested_mapping(payload.get("exporters", {}))
    collectors = _nested_mapping(payload.get("collectors", {}))
    validators = _nested_mapping(payload.get("validators", {}))
    system_cfg = _nested_mapping(collectors.get("system", {}))

    metric_names = [str(item).strip() for item in payload.get("metrics", []) if str(item).strip()]

    return ObservabilityConfig(
        profile_id=f"metrics/{normalized_profile}",
        artifact_root=_payload_string(exporters.get("artifact_root"), default="artifacts"),
        reports_root=_payload_string(exporters.get("reports_root"), default="reports"),
        runtime_index_filename=_payload_string(
            exporters.get("runtime_index_filename"),
            default="trace_index.csv",
        ),
        benchmark_index_filename=_payload_string(
            exporters.get("benchmark_index_filename"),
            default="trace_index.csv",
        ),
        export_json=_payload_bool(exporters.get("json"), default=True),
        export_csv=_payload_bool(exporters.get("csv"), default=True),
        include_system_metrics=_payload_bool(system_cfg.get("enabled"), default=True),
        include_gpu_metrics=_payload_bool(system_cfg.get("include_gpu"), default=True),
        warn_only=_payload_bool(validators.get("warn_only"), default=True),
        require_ordered_timestamps=_payload_bool(
            validators.get("require_ordered_timestamps"),
            default=True,
        ),
        metric_names=metric_names,
    )
