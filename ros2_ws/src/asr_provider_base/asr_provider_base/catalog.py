"""Provider profile UI/runtime catalog helpers.

This module keeps preset resolution out of the GUI and out of runtime nodes so the
same execution semantics can be reused by gateway, runtime orchestration, and
benchmark execution.
"""

from __future__ import annotations

from typing import Any


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def provider_ui(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the UI-specific provider metadata block from a provider profile."""
    ui = payload.get("ui", {})
    return ui if isinstance(ui, dict) else {}


def provider_presets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand provider UI presets into normalized rows used by gateway/runtime code."""
    ui = provider_ui(payload)
    raw = ui.get("model_presets", {})
    if not isinstance(raw, dict):
        return []
    rows: list[dict[str, Any]] = []
    for preset_id, meta in raw.items():
        if not isinstance(meta, dict):
            continue
        rows.append(
            {
                "preset_id": str(preset_id),
                "label": str(meta.get("label", preset_id)),
                "description": str(meta.get("description", "")),
                "quality_tier": str(meta.get("quality_tier", "balanced")),
                "resource_tier": str(meta.get("resource_tier", "medium")),
                "estimated_cost_tier": str(meta.get("estimated_cost_tier", "unknown")),
                "estimated_cost_usd_per_min": float(
                    meta.get("estimated_cost_usd_per_min", 0.0) or 0.0
                ),
                "settings": dict(meta.get("settings", {})),
                "tags": [str(item) for item in meta.get("tags", [])],
            }
        )
    return rows


def default_preset_id(payload: dict[str, Any]) -> str:
    """Return the explicitly configured or first available provider preset ID."""
    ui = provider_ui(payload)
    explicit = str(ui.get("default_model_preset", "")).strip()
    if explicit:
        return explicit
    presets = provider_presets(payload)
    return presets[0]["preset_id"] if presets else ""


def resolve_provider_execution(
    payload: dict[str, Any],
    *,
    preset_id: str = "",
    settings_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve final provider settings after applying preset and explicit overrides."""
    settings = payload.get("settings", {})
    base_settings = dict(settings) if isinstance(settings, dict) else {}
    selected_preset = str(preset_id or default_preset_id(payload) or "").strip()
    preset_meta: dict[str, Any] = {}
    for row in provider_presets(payload):
        if row["preset_id"] == selected_preset:
            preset_meta = row
            break
    merged = dict(base_settings)
    if preset_meta:
        merged = _deep_merge(merged, dict(preset_meta.get("settings", {})))
    explicit = settings_overrides or {}
    if explicit:
        merged = _deep_merge(merged, explicit)
    return {
        "settings": merged,
        "selected_preset": selected_preset,
        "preset": preset_meta,
    }
