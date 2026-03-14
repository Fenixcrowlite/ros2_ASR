"""Vosk local provider adapter."""

from __future__ import annotations

from typing import Any

from asr_backend_vosk.backend import VoskAsrBackend
from asr_core.models import AsrRequest
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus


def _normalize(provider_id: str, audio: ProviderAudio, response: Any) -> NormalizedAsrResult:
    words = [
        NormalizedWord(
            word=item.word,
            start_sec=float(item.start_sec),
            end_sec=float(item.end_sec),
            confidence=float(item.confidence),
            confidence_available=item.confidence > 0,
        )
        for item in response.word_timestamps
    ]
    return NormalizedAsrResult(
        request_id=audio.request_id,
        session_id=audio.session_id,
        provider_id=provider_id,
        text=response.text,
        is_final=True,
        is_partial=False,
        utterance_start_sec=words[0].start_sec if words else 0.0,
        utterance_end_sec=words[-1].end_sec if words else 0.0,
        words=words,
        confidence=float(response.confidence),
        confidence_available=response.confidence > 0,
        timestamps_available=bool(words),
        language=response.language,
        latency=LatencyMetadata(total_ms=float(response.timings.total_ms)),
        degraded=not response.success,
        error_code=response.error_code,
        error_message=response.error_message,
    )


class VoskProvider(AsrProviderAdapter):
    provider_id = "vosk"

    def __init__(self) -> None:
        self._backend: VoskAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._stream_chunks: list[bytes] = []
        self._stream_language = "en-US"
        self._stream_rate = 16000

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        del credentials_ref
        self._backend = VoskAsrBackend(config=config)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._backend is None:
            return ["Provider is not initialized"]
        if not self._backend.model_path:
            return ["model_path is required for Vosk"]
        return []

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=True,
            supports_confidence=True,
            supports_language_auto_detect=False,
            supports_cpu=True,
            supports_gpu=False,
            requires_network=False,
            cost_model_type="local",
        )

    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        del options
        if self._backend is None:
            raise RuntimeError("VoskProvider is not initialized")
        req = AsrRequest(
            wav_path=audio.wav_path or None,
            audio_bytes=audio.audio_bytes or None,
            language=audio.language,
            enable_word_timestamps=audio.enable_word_timestamps,
            sample_rate=audio.sample_rate_hz,
            metadata=audio.metadata,
        )
        resp = self._backend.recognize_once(req)
        return _normalize(self.provider_id, audio, resp)

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        opts = options or {}
        self._stream_chunks = []
        self._stream_language = str(opts.get("language", "en-US"))
        self._stream_rate = int(opts.get("sample_rate_hz", 16000))
        self._status = ProviderStatus(provider_id=self.provider_id, state="streaming")

    def push_audio(self, chunk: bytes) -> None:
        self._stream_chunks.append(chunk)

    def stop_stream(self) -> NormalizedAsrResult:
        if self._backend is None:
            raise RuntimeError("VoskProvider is not initialized")
        resp = self._backend.streaming_recognize(
            self._stream_chunks,
            language=self._stream_language,
            sample_rate=self._stream_rate,
        )
        audio = ProviderAudio(
            session_id="stream",
            request_id="stream",
            language=self._stream_language,
            sample_rate_hz=self._stream_rate,
        )
        return _normalize(self.provider_id, audio, resp)

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
