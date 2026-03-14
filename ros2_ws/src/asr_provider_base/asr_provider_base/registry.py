"""Provider adapter registry and factory."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from asr_provider_base.adapter import AsrProviderAdapter

_REGISTRY: dict[str, type[AsrProviderAdapter]] = {}
_DEFAULT_IMPORTS: dict[str, tuple[str, str]] = {
    "whisper": ("asr_provider_whisper.whisper_provider", "WhisperProvider"),
    "vosk": ("asr_provider_vosk.vosk_provider", "VoskProvider"),
    "azure": ("asr_provider_azure.azure_provider", "AzureProvider"),
    "google": ("asr_provider_google.google_provider", "GoogleProvider"),
    "aws": ("asr_provider_aws.aws_provider", "AwsProvider"),
}


def register_provider(provider_id: str, cls: type[AsrProviderAdapter]) -> None:
    _REGISTRY[provider_id] = cls


def list_providers() -> list[str]:
    return sorted(set(_REGISTRY.keys()) | set(_DEFAULT_IMPORTS.keys()))


def _ensure_provider(provider_id: str) -> None:
    if provider_id in _REGISTRY:
        return
    if provider_id not in _DEFAULT_IMPORTS:
        raise ValueError(f"Unknown provider adapter: {provider_id}")
    module_name, class_name = _DEFAULT_IMPORTS[provider_id]
    module = import_module(module_name)
    cls = getattr(module, class_name)
    _REGISTRY[provider_id] = cls


def create_provider(provider_id: str, **kwargs: Any) -> AsrProviderAdapter:
    _ensure_provider(provider_id)
    return _REGISTRY[provider_id](**kwargs)
