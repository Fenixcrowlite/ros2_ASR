"""Helpers for selecting the active provider from runtime config payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderSelection:
    """Resolved runtime provider choice plus preset and settings overrides."""

    profile: str
    preset: str = ""
    settings: dict[str, object] = field(default_factory=dict)


def normalize_provider_profile_id(value: str) -> str:
    """Normalize short provider IDs into `providers/<id>` profile references."""
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("providers/"):
        return text
    return f"providers/{text}"


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def resolve_provider_selection_from_runtime_payload(
    payload: dict[str, Any],
    *,
    fallback_profile: str = "providers/whisper_local",
) -> ProviderSelection:
    """Resolve the runtime-selected provider using new and legacy keys."""
    orchestrator = _as_mapping(payload.get("orchestrator", {}))
    providers = _as_mapping(payload.get("providers", {}))
    settings = _as_mapping(providers.get("settings", {}))

    active_profile = normalize_provider_profile_id(
        str(providers.get("active", "") or orchestrator.get("provider_profile", "") or "")
    ) or normalize_provider_profile_id(fallback_profile)
    preset = str(providers.get("preset", "") or orchestrator.get("provider_preset", "") or "")
    return ProviderSelection(
        profile=active_profile,
        preset=preset,
        settings=settings,
    )
