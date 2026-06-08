"""High-level provider manager using profile-driven config and secret references."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from asr_config import load_secret_ref, resolve_profile, resolve_secret_ref

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.catalog import resolve_provider_execution
from asr_provider_base.registry import create_provider

_PROVIDER_EXECUTION_SIGNATURES: set[str] = set()


def _provider_execution_signature(
    *,
    provider_profile: str,
    provider_id: str,
    settings: dict[str, Any],
    credentials_ref_path: str,
    adapter_path: str,
) -> str:
    payload = {
        "provider_profile": provider_profile,
        "provider_id": provider_id,
        "settings": settings,
        "credentials_ref_path": credentials_ref_path,
        "adapter_path": adapter_path,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _set_provider_runtime_metadata(provider: AsrProviderAdapter, **kwargs: Any) -> None:
    for key, value in kwargs.items():
        setattr(provider, key, value)


def provider_runtime_metadata(
    provider: AsrProviderAdapter,
    *,
    record_invocation: bool = False,
) -> dict[str, Any]:
    """Project cold-start and invocation metadata tracked on the adapter instance."""
    invocation_count = int(getattr(provider, "_asr_provider_invocation_count", 0) or 0)
    call_cold_start = invocation_count == 0
    if record_invocation:
        _set_provider_runtime_metadata(
            provider,
            _asr_provider_invocation_count=invocation_count + 1,
        )
    return {
        "model_load_ms": float(getattr(provider, "_asr_model_load_ms", 0.0) or 0.0),
        "provider_init_cold_start": bool(
            getattr(provider, "_asr_provider_init_cold_start", False)
        ),
        "provider_init_warm_start": not bool(
            getattr(provider, "_asr_provider_init_cold_start", False)
        ),
        "provider_call_cold_start": call_cold_start,
        "provider_call_warm_start": not call_cold_start,
        "provider_invocation_index": invocation_count + (1 if record_invocation else 0),
    }


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
        adapter_path = str(payload.get("adapter", "") or "").strip()
        execution_signature = _provider_execution_signature(
            provider_profile=provider_profile,
            provider_id=provider_id,
            settings=settings,
            credentials_ref_path=credentials_ref_path,
            adapter_path=adapter_path,
        )
        init_started_ns = time.perf_counter_ns()
        provider = create_provider(
            provider_id,
            adapter_path=adapter_path,
            configs_root=self.configs_root,
        )
        provider.initialize(config=settings, credentials_ref=credentials)
        errors = provider.validate_config()
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"Provider config validation failed: {joined}")
        model_load_ms = max((time.perf_counter_ns() - init_started_ns) / 1_000_000.0, 0.0)
        init_cold_start = execution_signature not in _PROVIDER_EXECUTION_SIGNATURES
        _PROVIDER_EXECUTION_SIGNATURES.add(execution_signature)
        _set_provider_runtime_metadata(
            provider,
            _asr_provider_profile=provider_profile,
            _asr_provider_execution_signature=execution_signature,
            _asr_model_load_ms=model_load_ms,
            _asr_provider_init_cold_start=init_cold_start,
            _asr_provider_invocation_count=0,
        )
        return provider
