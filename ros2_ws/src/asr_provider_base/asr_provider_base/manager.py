"""High-level provider manager using profile-driven config and secret references."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asr_config import load_secret_ref, resolve_profile, resolve_secret_ref
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.registry import create_provider


class ProviderManager:
    """Resolve provider profile and create initialized provider adapters."""

    def __init__(self, configs_root: str = "configs") -> None:
        self.configs_root = configs_root

    def create_from_profile(self, provider_profile: str) -> AsrProviderAdapter:
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

        settings = payload.get("settings", {})
        if not isinstance(settings, dict):
            raise ValueError("Provider profile settings must be an object")

        credentials_ref_path = str(payload.get("credentials_ref", "")).strip()
        credentials: dict[str, str] = {}
        if credentials_ref_path:
            ref_path = Path(credentials_ref_path)
            if not ref_path.is_absolute():
                ref_path = Path(self.configs_root).parent / credentials_ref_path
            secret_ref = load_secret_ref(str(ref_path))
            credentials = resolve_secret_ref(secret_ref)

        provider = create_provider(provider_id)
        provider.initialize(config=settings, credentials_ref=credentials)
        errors = provider.validate_config()
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"Provider config validation failed: {joined}")
        return provider
