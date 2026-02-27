"""Base interface every ASR backend must implement."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterable

from asr_core.audio import pcm_chunks_to_wav_bytes
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities


class AsrBackend(ABC):
    """Abstract backend contract.

    Implementations must provide at least `recognize_once`.
    `streaming_recognize` has a safe default that buffers chunks and delegates
    to one-shot recognition.
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
        """Default streaming fallback for non-native streaming providers.

        Flow:
        1. Buffer all PCM chunks.
        2. Convert them to valid WAV bytes.
        3. Call `recognize_once`.
        """
        start = time.perf_counter()
        buffered_chunks = list(chunks)
        wav_bytes = pcm_chunks_to_wav_bytes(buffered_chunks, sample_rate=sample_rate)
        request = AsrRequest(audio_bytes=wav_bytes, language=language, sample_rate=sample_rate)
        result = self.recognize_once(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result.timings = AsrTimings(
            preprocess_ms=result.timings.preprocess_ms,
            inference_ms=result.timings.inference_ms,
            postprocess_ms=max(
                result.timings.postprocess_ms,
                elapsed_ms - result.timings.preprocess_ms - result.timings.inference_ms,
            ),
        )
        if self.capabilities.streaming_mode == "none":
            result.backend_info["streaming_fallback"] = "true"
        return result
