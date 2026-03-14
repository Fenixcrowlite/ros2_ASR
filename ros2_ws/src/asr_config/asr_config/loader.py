"""Profile-driven configuration resolver.

Override precedence (later wins):
1) base defaults
2) deployment defaults
3) selected profile (with inheritance)
4) related profile set (provider/dataset/metric)
5) launch overrides
6) env overrides
7) ROS parameter overrides
8) session temporary overrides
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from asr_config.models import ResolvedConfig


PROFILE_DIRS = {
    "runtime": "runtime",
    "providers": "providers",
    "benchmark": "benchmark",
    "datasets": "datasets",
    "metrics": "metrics",
    "deployment": "deployment",
    "gui": "gui",
}


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
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _profile_file(root: Path, profile_type: str, profile_id: str) -> Path:
    rel = PROFILE_DIRS.get(profile_type, profile_type)
    filename = profile_id
    if not filename.endswith(".yaml"):
        filename = f"{filename}.yaml"
    return root / rel / filename


def _resolve_profile_tree(
    root: Path,
    profile_type: str,
    profile_id: str,
    merge_order: list[str],
    visited: set[str],
) -> dict[str, Any]:
    marker = f"{profile_type}:{profile_id}"
    if marker in visited:
        raise ValueError(f"Circular profile inheritance detected: {marker}")
    visited.add(marker)

    path = _profile_file(root, profile_type, profile_id)
    payload = _load_yaml(path)

    merged: dict[str, Any] = {}
    inherits = payload.get("inherits", [])
    if isinstance(inherits, str):
        inherits = [inherits]
    if not isinstance(inherits, list):
        raise ValueError(f"inherits must be list or string: {path}")

    for inherited in inherits:
        inherited_id = str(inherited).strip()
        if not inherited_id:
            continue
        merged = _deep_merge(
            merged,
            _resolve_profile_tree(
                root=root,
                profile_type=profile_type,
                profile_id=inherited_id,
                merge_order=merge_order,
                visited=visited,
            ),
        )

    merge_order.append(str(path))
    return _deep_merge(merged, payload)


def _env_overrides(prefix: str = "ASR_CFG__") -> dict[str, Any]:
    """Read env overrides using dotted paths.

    Example:
      ASR_CFG__orchestrator.provider_profile=providers/azure_cloud
    """
    out: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].strip()
        if not path:
            continue
        cursor: dict[str, Any] = out
        tokens = [token for token in path.split(".") if token]
        for token in tokens[:-1]:
            cursor = cursor.setdefault(token, {})
            if not isinstance(cursor, dict):
                break
        if tokens:
            cursor[tokens[-1]] = value
    return out


def snapshot_resolved_config(
    *,
    profile_type: str,
    profile_id: str,
    payload: dict[str, Any],
    resolved_root: Path,
) -> str:
    resolved_root.mkdir(parents=True, exist_ok=True)
    filename = f"{profile_type}__{profile_id.replace('/', '_')}.json"
    path = resolved_root / filename
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return str(path)


def resolve_profile(
    *,
    profile_type: str,
    profile_id: str,
    configs_root: str = "configs",
    deployment_profile: str = "dev_local",
    related_profiles: dict[str, str] | None = None,
    launch_overrides: dict[str, Any] | None = None,
    env_overrides: dict[str, Any] | None = None,
    ros_param_overrides: dict[str, Any] | None = None,
    session_overrides: dict[str, Any] | None = None,
    write_snapshot: bool = True,
) -> ResolvedConfig:
    """Resolve profile with deterministic merge precedence."""
    root = Path(configs_root)
    merge_order: list[str] = []

    base_defaults = _load_yaml(root / PROFILE_DIRS.get(profile_type, profile_type) / "_base.yaml")
    if base_defaults:
        merge_order.append(
            str(root / PROFILE_DIRS.get(profile_type, profile_type) / "_base.yaml")
        )

    deployment_defaults = _load_yaml(root / "deployment" / f"{deployment_profile}.yaml")
    if deployment_defaults:
        merge_order.append(str(root / "deployment" / f"{deployment_profile}.yaml"))

    profile_data = _resolve_profile_tree(
        root=root,
        profile_type=profile_type,
        profile_id=profile_id,
        merge_order=merge_order,
        visited=set(),
    )

    merged = _deep_merge(base_defaults, deployment_defaults)
    merged = _deep_merge(merged, profile_data)

    for rel_type, rel_id in (related_profiles or {}).items():
        rel_payload = _resolve_profile_tree(
            root=root,
            profile_type=rel_type,
            profile_id=rel_id,
            merge_order=merge_order,
            visited=set(),
        )
        merged = _deep_merge(merged, {rel_type: rel_payload})

    if launch_overrides:
        merged = _deep_merge(merged, launch_overrides)
        merge_order.append("launch_overrides")

    merged_env = _deep_merge(_env_overrides(), env_overrides or {})
    if merged_env:
        merged = _deep_merge(merged, merged_env)
        merge_order.append("env_overrides")

    if ros_param_overrides:
        merged = _deep_merge(merged, ros_param_overrides)
        merge_order.append("ros_param_overrides")

    if session_overrides:
        merged = _deep_merge(merged, session_overrides)
        merge_order.append("session_overrides")

    snapshot_path = ""
    if write_snapshot:
        snapshot_path = snapshot_resolved_config(
            profile_type=profile_type,
            profile_id=profile_id,
            payload=merged,
            resolved_root=root / "resolved",
        )

    return ResolvedConfig(
        profile_type=profile_type,
        profile_id=profile_id,
        data=merged,
        merge_order=merge_order,
        snapshot_path=snapshot_path,
    )


def list_profiles(profile_type: str, configs_root: str = "configs") -> list[str]:
    """List profile IDs for a given profile type."""
    root = Path(configs_root)
    folder = root / PROFILE_DIRS.get(profile_type, profile_type)
    if not folder.exists():
        return []
    return sorted(path.stem for path in folder.glob("*.yaml") if not path.stem.startswith("_"))
