"""High-level provider manager using profile-driven config and secret references."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asr_config import load_secret_ref, resolve_profile, resolve_secret_ref

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.catalog import resolve_provider_execution
from asr_provider_base.registry import create_provider


class ProviderManager:
    """Resolve provider profile and create initialized provider adapters.

    This is the bridge between human-facing YAML profiles and concrete Python
    provider classes. Runtime, benchmark, and gateway code all use the same
    manager so provider setup rules stay consistent everywhere.
    """

    def __init__(self, configs_root: str = "configs") -> None:
        self.configs_root = configs_root

    def resolve_profile_payload(self, provider_profile: str) -> dict[str, Any]:
        profile_id = provider_profile
        if provider_profile.startswith("providers/"):
            profile_id = provider_profile.split("/", 1)[1]
        resolved = resolve_profile(
            profile_type="providers",
            profile_id=profile_id,
            configs_root=self.configs_root,
        )
        payload = resolved.data
        provider_id = str(payload.get("provider_id", "")).strip()
        if not provider_id:
            raise ValueError("Provider profile is missing provider_id")
        return payload

    def create_from_profile(
        self,
        provider_profile: str,
        *,
        preset_id: str = "",
        settings_overrides: dict[str, Any] | None = None,
    ) -> AsrProviderAdapter:
        # 1. Load the YAML profile and determine which provider family it uses.
        payload = self.resolve_profile_payload(provider_profile)
        provider_id = str(payload.get("provider_id", "")).strip()

        # 2. Merge base settings from the profile with the selected UI preset
        # and any explicit overrides coming from gateway/runtime requests.
        execution = resolve_provider_execution(
            payload,
            preset_id=preset_id,
            settings_overrides=settings_overrides or {},
        )
        settings = execution["settings"]
        if not isinstance(settings, dict):
            raise ValueError("Provider profile settings must be an object")

        # 3. Resolve the optional credentials_ref into a plain key/value map
        # that the provider adapter can consume without knowing repo layout.
        credentials_ref_path = str(payload.get("credentials_ref", "")).strip()
        credentials: dict[str, str] = {}
        if credentials_ref_path:
            ref_path = Path(credentials_ref_path)
            if not ref_path.is_absolute():
                ref_path = Path(self.configs_root).parent / credentials_ref_path
            secret_ref = load_secret_ref(str(ref_path))
            credentials = resolve_secret_ref(secret_ref)

        # 4. Instantiate and validate the adapter before handing it to caller.
        provider = create_provider(
            provider_id,
            adapter_path=str(payload.get("adapter", "") or "").strip(),
        )
        provider.initialize(config=settings, credentials_ref=credentials)
        errors = provider.validate_config()
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"Provider config validation failed: {joined}")
        return provider
