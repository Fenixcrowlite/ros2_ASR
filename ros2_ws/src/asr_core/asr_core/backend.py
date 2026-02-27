from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterable

from asr_core.audio import pcm_chunks_to_wav_bytes
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities


class AsrBackend(ABC):
    name = "base"

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        self.config = config or {}
        self.client = client

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities()

    def has_credentials(self) -> bool:
        return True

    @abstractmethod
    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        raise NotImplementedError

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
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
