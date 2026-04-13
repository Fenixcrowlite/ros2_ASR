"""Abstract provider adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from asr_core.normalized import NormalizedAsrResult

from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import (
    ProviderAudio,
    ProviderMetadata,
    ProviderRuntimeMetrics,
    ProviderStatus,
)


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

    def stream_recognize(
        self,
        chunks: Iterable[bytes],
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedAsrResult]:
        """Convenience adapter flow for callers that prefer one streaming method."""
        results: list[NormalizedAsrResult] = []
        self.start_stream(options)
        for chunk in chunks:
            partial = self.push_audio(chunk)
            if partial is not None:
                results.append(partial)
            results.extend(self.drain_stream_results())
        final = self.stop_stream()
        results.extend(self.drain_stream_results())
        results.append(final)
        return results

    @abstractmethod
    def stop_stream(self) -> NormalizedAsrResult:
        """Stop stream and return final result."""

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Return provider status snapshot."""

    @abstractmethod
    def teardown(self) -> None:
        """Release provider resources."""

    def get_metadata(self) -> ProviderMetadata:
        """Expose provider identity and implementation metadata."""
        metadata = getattr(self, "_provider_metadata", None)
        if isinstance(metadata, ProviderMetadata):
            return metadata
        return ProviderMetadata(provider_id=str(getattr(self, "provider_id", "base") or "base"))

    def get_metrics(self) -> ProviderRuntimeMetrics:
        """Expose provider-side runtime metrics that complement benchmark metrics."""
        metrics = getattr(self, "_provider_metrics", None)
        if isinstance(metrics, ProviderRuntimeMetrics):
            return metrics
        return ProviderRuntimeMetrics(
            model_load_ms=float(getattr(self, "_asr_model_load_ms", 0.0) or 0.0),
            requests_total=int(getattr(self, "_provider_request_count", 0) or 0),
            stream_sessions_total=int(getattr(self, "_provider_stream_session_count", 0) or 0),
            last_latency_ms=float(getattr(self, "_provider_last_latency_ms", 0.0) or 0.0),
            average_latency_ms=float(
                getattr(self, "_provider_average_latency_ms", 0.0) or 0.0
            ),
            errors_total=int(getattr(self, "_provider_error_count", 0) or 0),
            last_error_code=str(getattr(self, "_provider_last_error_code", "") or ""),
            last_error_message=str(getattr(self, "_provider_last_error_message", "") or ""),
        )
