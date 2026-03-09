"""Deterministic backend used for tests, CI, and smoke checks."""

from __future__ import annotations

import time
import wave
from collections.abc import Iterable
from pathlib import Path

from asr_core.audio import wav_duration_sec
from asr_core.backend import AsrBackend
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp


@register_backend("mock")
class MockAsrBackend(AsrBackend):
    """Backend that returns predictable transcripts without ML inference."""

    name = "mock"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=True,
            streaming_mode="native",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=False,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        """Read deterministic latency and optional filename->transcript map."""
        super().__init__(config=config, client=client)
        self.latency_ms = float(self.config.get("deterministic_latency_ms", 25.0))
        self.transcript_map = dict(self.config.get("transcript_map", {}))

    def _resolve_text(self, request: AsrRequest) -> str:
        """Pick transcript from map or fallback synthetic phrase."""
        if request.wav_path:
            key = Path(request.wav_path).name
            if key in self.transcript_map:
                return self.transcript_map[key]
            return f"mock transcript {key}"
        return "mock transcript from bytes"

    def _duration(self, request: AsrRequest) -> float:
        """Estimate audio duration from WAV or bytes."""
        if request.wav_path:
            return wav_duration_sec(request.wav_path)
        if request.audio_bytes:
            return len(request.audio_bytes) / float(max(request.sample_rate * 2, 1))
        return 0.0

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Return deterministic one-shot ASR response."""
        language = normalize_language_code(request.language, fallback="en-US")
        try:
            text = self._resolve_text(request)
            duration = self._duration(request)
        except FileNotFoundError as exc:
            return AsrResponse(
                success=False,
                error_code="file_missing",
                error_message=str(exc),
                language=language,
                backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
            )
        except wave.Error as exc:
            return AsrResponse(
                success=False,
                error_code="invalid_audio",
                error_message=str(exc),
                language=language,
                backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
            )
        except Exception as exc:
            return AsrResponse(
                success=False,
                error_code="mock_runtime_error",
                error_message=str(exc),
                language=language,
                backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
            )

        start = time.perf_counter()
        time.sleep(self.latency_ms / 1000.0)
        inference_ms = (time.perf_counter() - start) * 1000.0

        words = text.split()
        wts: list[WordTimestamp] = []
        if words and duration > 0:
            step = duration / len(words)
            for idx, word in enumerate(words):
                wts.append(
                    WordTimestamp(
                        word=word,
                        start_sec=idx * step,
                        end_sec=(idx + 1) * step,
                        confidence=0.99,
                    )
                )

        return AsrResponse(
            text=text,
            partials=words[:-1] if len(words) > 1 else words,
            confidence=0.99,
            word_timestamps=wts if request.enable_word_timestamps else [],
            language=language,
            backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
            timings=AsrTimings(preprocess_ms=1.0, inference_ms=inference_ms, postprocess_ms=1.0),
            audio_duration_sec=duration,
            success=True,
        )

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        """Return deterministic streaming response with synthetic partials."""
        chunks_list = list(chunks)
        partials = [f"partial_{i}" for i in range(1, len(chunks_list) + 1)]
        text = "streaming mock transcript"
        normalized_language = normalize_language_code(language, fallback="en-US")
        duration = sum(len(c) for c in chunks_list) / float(max(sample_rate * 2, 1))
        time.sleep(self.latency_ms / 1000.0)
        return AsrResponse(
            text=text,
            partials=partials,
            confidence=0.98,
            word_timestamps=[],
            language=normalized_language,
            backend_info={"provider": "mock", "model": "deterministic", "region": "local"},
            timings=AsrTimings(preprocess_ms=1.0, inference_ms=self.latency_ms, postprocess_ms=1.0),
            audio_duration_sec=duration,
            success=True,
        )
