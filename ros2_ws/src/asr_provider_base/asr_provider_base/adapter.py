"""Abstract provider adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from asr_core.normalized import NormalizedAsrResult
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus


class AsrProviderAdapter(ABC):
    """Unified provider adapter contract for runtime and benchmark use."""

    provider_id = "base"

    @abstractmethod
    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        """Initialize SDK/resources for this provider."""

    @abstractmethod
    def validate_config(self) -> list[str]:
        """Validate provider settings and return list of errors."""

    @abstractmethod
    def discover_capabilities(self) -> ProviderCapabilities:
        """Expose provider capability matrix."""

    @abstractmethod
    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        """Run one-shot recognition."""

    @abstractmethod
    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        """Start streaming session when supported."""

    @abstractmethod
    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        """Push stream chunk and optionally return a partial result."""

    def drain_stream_results(self) -> list[NormalizedAsrResult]:
        """Return any already-produced non-final stream updates.

        Native cloud SDKs often emit interim hypotheses asynchronously from
        the audio push cadence. Adapters can override this hook to expose those
        updates without forcing the runtime layer to know provider internals.
        """
        return []

    @abstractmethod
    def stop_stream(self) -> NormalizedAsrResult:
        """Stop stream and return final result."""

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Return provider status snapshot."""

    @abstractmethod
    def teardown(self) -> None:
        """Release provider resources."""
