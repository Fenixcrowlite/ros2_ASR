"""Provider adapter base package."""

from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.adapters import (
    backend_info_float,
    normalize_backend_response,
    normalize_words,
)
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.catalog import (
    default_preset_id,
    provider_presets,
    provider_ui,
    resolve_provider_execution,
)
from asr_provider_base.config import (
    ProviderSelection,
    normalize_provider_profile_id,
    resolve_provider_selection_from_runtime_payload,
)
from asr_provider_base.manager import ProviderManager, provider_runtime_metadata
from asr_provider_base.models import (
    ProviderAudio,
    ProviderMetadata,
    ProviderRuntimeMetrics,
    ProviderStatus,
)
from asr_provider_base.registry import create_provider, list_providers, register_provider

__all__ = [
    "AsrProviderAdapter",
    "ProviderCapabilities",
    "ProviderAudio",
    "ProviderMetadata",
    "ProviderRuntimeMetrics",
    "ProviderStatus",
    "ProviderSelection",
    "ProviderManager",
    "provider_runtime_metadata",
    "provider_ui",
    "provider_presets",
    "default_preset_id",
    "resolve_provider_execution",
    "normalize_provider_profile_id",
    "resolve_provider_selection_from_runtime_payload",
    "backend_info_float",
    "normalize_words",
    "normalize_backend_response",
    "create_provider",
    "list_providers",
    "register_provider",
]
