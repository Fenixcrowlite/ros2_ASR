from __future__ import annotations

from collections.abc import Callable
from importlib import import_module

from asr_core.backend import AsrBackend

RegistryType = dict[str, type[AsrBackend]]
_REGISTRY: RegistryType = {}

_BACKEND_IMPORTS: dict[str, tuple[str, str]] = {
    "mock": ("asr_backend_mock.backend", "MockAsrBackend"),
    "vosk": ("asr_backend_vosk.backend", "VoskAsrBackend"),
    "whisper": ("asr_backend_whisper.backend", "WhisperAsrBackend"),
    "google": ("asr_backend_google.backend", "GoogleAsrBackend"),
    "aws": ("asr_backend_aws.backend", "AwsAsrBackend"),
    "azure": ("asr_backend_azure.backend", "AzureAsrBackend"),
}


def register_backend(name: str) -> Callable[[type[AsrBackend]], type[AsrBackend]]:
    def wrapper(cls: type[AsrBackend]) -> type[AsrBackend]:
        _REGISTRY[name] = cls
        return cls

    return wrapper


def get_registered_backends() -> list[str]:
    return sorted(_REGISTRY.keys())


def _ensure_imported(name: str) -> None:
    if name in _REGISTRY:
        return
    if name not in _BACKEND_IMPORTS:
        raise ValueError(f"Unknown backend '{name}'")
    module_name, class_name = _BACKEND_IMPORTS[name]
    module = import_module(module_name)
    cls = getattr(module, class_name)
    _REGISTRY[name] = cls


def create_backend(
    name: str, config: dict | None = None, client: object | None = None
) -> AsrBackend:
    _ensure_imported(name)
    backend_cls = _REGISTRY[name]
    return backend_cls(config=config or {}, client=client)
