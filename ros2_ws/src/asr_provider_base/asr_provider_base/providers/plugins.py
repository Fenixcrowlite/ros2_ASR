"""Discovery of provider plugins declared by config or environment."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(slots=True)
class ProviderPluginSpec:
    provider_id: str
    adapter_path: str = ""
    source: str = "profile"
    profile_id: str = ""


def _snake_case(value: str) -> str:
    text = _CAMEL_BOUNDARY_RE.sub("_", str(value or ""))
    normalized = _NON_ALNUM_RE.sub("_", text.strip().lower()).strip("_")
    return normalized


def _provider_id_from_adapter_path(adapter_path: str) -> str:
    class_name = str(adapter_path or "").strip().rsplit(".", 1)[-1]
    provider_id = _snake_case(class_name)
    for suffix in ("_provider", "_adapter"):
        if provider_id.endswith(suffix):
            provider_id = provider_id[: -len(suffix)]
    return provider_id


def _load_yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _profile_provider_specs(configs_root: str = "configs") -> dict[str, ProviderPluginSpec]:
    folder = Path(configs_root) / "providers"
    if not folder.exists():
        return {}
    specs: dict[str, ProviderPluginSpec] = {}
    for path in sorted(folder.glob("*.yaml")):
        if path.stem.startswith("_"):
            continue
        payload = _load_yaml(path)
        provider_id = str(payload.get("provider_id", "") or "").strip()
        adapter_path = str(payload.get("adapter", "") or "").strip()
        if not provider_id and adapter_path:
            provider_id = _provider_id_from_adapter_path(adapter_path)
        if not provider_id:
            continue
        specs[provider_id] = ProviderPluginSpec(
            provider_id=provider_id,
            adapter_path=adapter_path,
            source="profile",
            profile_id=f"providers/{path.stem}",
        )
    return specs


def _env_provider_specs() -> dict[str, ProviderPluginSpec]:
    raw = str(os.getenv("ASR_PROVIDER_PLUGIN_MODULES", "") or "").strip()
    if not raw:
        return {}
    specs: dict[str, ProviderPluginSpec] = {}
    for item in raw.split(","):
        entry = str(item or "").strip()
        if not entry:
            continue
        if "=" in entry:
            provider_id, adapter_path = entry.split("=", 1)
        else:
            adapter_path = entry
            provider_id = _provider_id_from_adapter_path(adapter_path)
        normalized_provider_id = str(provider_id or "").strip()
        normalized_adapter_path = str(adapter_path or "").strip()
        if not normalized_provider_id or not normalized_adapter_path:
            continue
        specs[normalized_provider_id] = ProviderPluginSpec(
            provider_id=normalized_provider_id,
            adapter_path=normalized_adapter_path,
            source="env",
        )
    return specs


def discover_provider_plugins(configs_root: str = "configs") -> dict[str, ProviderPluginSpec]:
    """Discover provider plugins without importing heavy provider modules."""
    specs = _profile_provider_specs(configs_root=configs_root)
    specs.update(_env_provider_specs())
    return specs
