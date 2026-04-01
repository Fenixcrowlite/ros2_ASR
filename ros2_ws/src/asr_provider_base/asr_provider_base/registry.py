"""Provider adapter registry and factory."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.providers import discover_provider_plugins

_REGISTRY: dict[str, type[AsrProviderAdapter]] = {}
_DEFAULT_IMPORTS: dict[str, tuple[str, str]] = {
    "whisper": ("asr_provider_whisper.whisper_provider", "WhisperProvider"),
    "vosk": ("asr_provider_vosk.vosk_provider", "VoskProvider"),
    "azure": ("asr_provider_azure.azure_provider", "AzureProvider"),
    "google": ("asr_provider_google.google_provider", "GoogleProvider"),
    "aws": ("asr_provider_aws.aws_provider", "AwsProvider"),
    "huggingface_local": (
        "asr_provider_huggingface.local_provider",
        "HuggingFaceLocalProvider",
    ),
    "huggingface_api": (
        "asr_provider_huggingface.api_provider",
        "HuggingFaceAPIProvider",
    ),
}


def register_provider(provider_id: str, cls: type[AsrProviderAdapter]) -> None:
    _REGISTRY[provider_id] = cls


def list_providers(*, configs_root: str = "configs") -> list[str]:
    discovered = discover_provider_plugins(configs_root=configs_root)
    return sorted(set(_REGISTRY.keys()) | set(_DEFAULT_IMPORTS.keys()) | set(discovered.keys()))


def _ensure_provider(provider_id: str) -> None:
    if provider_id in _REGISTRY:
        return
    if provider_id not in _DEFAULT_IMPORTS:
        raise ValueError(f"Unknown provider adapter: {provider_id}")
    module_name, class_name = _DEFAULT_IMPORTS[provider_id]
    module = import_module(module_name)
    cls = getattr(module, class_name)
    _REGISTRY[provider_id] = cls


def _provider_class_from_adapter_path(adapter_path: str) -> type[AsrProviderAdapter]:
    module_name, separator, class_name = str(adapter_path or "").strip().rpartition(".")
    if not separator or not module_name or not class_name:
        raise ValueError(f"Invalid provider adapter path: {adapter_path!r}")
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not isinstance(cls, type) or not issubclass(cls, AsrProviderAdapter):
        raise TypeError(
            "Provider adapter path does not resolve to AsrProviderAdapter: "
            f"{adapter_path}"
        )
    return cls


def create_provider(
    provider_id: str,
    *,
    adapter_path: str = "",
    configs_root: str = "configs",
    **kwargs: Any,
) -> AsrProviderAdapter:
    if str(adapter_path or "").strip():
        cls = _provider_class_from_adapter_path(adapter_path)
        return cls(**kwargs)
    discovered = discover_provider_plugins(configs_root=configs_root)
    plugin = discovered.get(provider_id)
    if plugin is not None and str(plugin.adapter_path or "").strip():
        cls = _provider_class_from_adapter_path(plugin.adapter_path)
        return cls(**kwargs)
    _ensure_provider(provider_id)
    return _REGISTRY[provider_id](**kwargs)
