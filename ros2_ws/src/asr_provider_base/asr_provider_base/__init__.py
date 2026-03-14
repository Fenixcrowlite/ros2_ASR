"""Provider adapter base package."""

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.manager import ProviderManager
from asr_provider_base.models import ProviderAudio, ProviderStatus
from asr_provider_base.registry import create_provider, list_providers, register_provider

__all__ = [
    "AsrProviderAdapter",
    "ProviderCapabilities",
    "ProviderAudio",
    "ProviderStatus",
    "ProviderManager",
    "create_provider",
    "list_providers",
    "register_provider",
]
