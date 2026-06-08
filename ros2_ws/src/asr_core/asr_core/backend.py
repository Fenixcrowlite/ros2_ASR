"""Base interface every ASR backend must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from asr_core.models import AsrRequest, AsrResponse, BackendCapabilities


class AsrBackend(ABC):
    """Abstract backend contract.

    Implementations must provide at least `recognize_once`.
    Backends that advertise streaming support must implement
    `streaming_recognize` explicitly instead of relying on a buffered fallback.
    """

    name = "base"

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        """Store backend configuration and optional injected SDK client."""
        self.config = config or {}
        self.client = client

    @property
    def capabilities(self) -> BackendCapabilities:
        """Return feature flags supported by concrete backend."""
        return BackendCapabilities()

    def has_credentials(self) -> bool:
        """Tell ROS status service if backend credentials are available."""
        return True

    @abstractmethod
    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Recognize a full phrase from WAV path or WAV bytes."""
        raise NotImplementedError

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        """Run provider-native streaming recognition.

        The base contract is intentionally strict: a backend must not silently
        buffer streaming input and reinterpret it as one-shot recognition.
        """
        del chunks, language, sample_rate
        backend_name = getattr(self, "name", self.__class__.__name__)
        if not self.capabilities.supports_streaming:
            raise NotImplementedError(f"{backend_name} does not support streaming_recognize")
        raise NotImplementedError(
            f"{backend_name} advertises streaming support but does not implement streaming_recognize"
        )
