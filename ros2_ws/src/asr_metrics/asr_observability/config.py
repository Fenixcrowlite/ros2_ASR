"""YAML-backed observability configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from asr_config import resolve_profile

DEFAULT_OBSERVABILITY_PROFILE = "default_observability"


@dataclass(slots=True)
class ObservabilityConfig:
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


def load_observability_config(
    *,
    configs_root: str = "configs",
    profile_id: str | None = None,
) -> ObservabilityConfig:
    requested = str(
        profile_id or os.getenv("ASR_METRICS_PROFILE") or DEFAULT_OBSERVABILITY_PROFILE
    ).strip()
    normalized_profile = (
        requested.split("/", 1)[1] if requested.startswith("metrics/") else requested
    )
    resolved = resolve_profile(
        profile_type="metrics",
        profile_id=normalized_profile,
        configs_root=configs_root,
        write_snapshot=False,
    )
    payload = resolved.data
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
