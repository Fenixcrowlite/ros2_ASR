"""Provider adapter base package."""

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.catalog import (
    default_preset_id,
    provider_presets,
    provider_ui,
    resolve_provider_execution,
)
from asr_provider_base.manager import ProviderManager, provider_runtime_metadata
from asr_provider_base.models import ProviderAudio, ProviderStatus
from asr_provider_base.registry import create_provider, list_providers, register_provider

__all__ = [
    "AsrProviderAdapter",
    "ProviderCapabilities",
    "ProviderAudio",
    "ProviderStatus",
    "ProviderManager",
    "provider_runtime_metadata",
    "provider_ui",
    "provider_presets",
    "default_preset_id",
    "resolve_provider_execution",
    "create_provider",
    "list_providers",
    "register_provider",
]
