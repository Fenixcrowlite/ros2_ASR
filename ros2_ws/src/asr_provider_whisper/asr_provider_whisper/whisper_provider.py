"""Whisper provider adapter (local baseline)."""

from __future__ import annotations

import audioop
import time
import wave
from typing import Any

from asr_backend_whisper.backend import WhisperAsrBackend
from asr_core.models import AsrRequest
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus


def _normalize(provider_id: str, audio: ProviderAudio, response: Any, is_partial: bool) -> NormalizedAsrResult:
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
        is_final=not is_partial,
        is_partial=is_partial,
        utterance_start_sec=words[0].start_sec if words else 0.0,
        utterance_end_sec=words[-1].end_sec if words else 0.0,
        words=words,
        confidence=float(response.confidence),
        confidence_available=response.confidence > 0,
        timestamps_available=bool(words),
        language=response.language,
        language_detected=False,
        latency=LatencyMetadata(
            total_ms=float(response.timings.total_ms),
            first_partial_ms=0.0,
            finalization_ms=float(response.timings.postprocess_ms),
        ),
        raw_metadata_ref="",
        degraded=not response.success,
        error_code=response.error_code,
        error_message=response.error_message,
        tags=[],
    )


class WhisperProvider(AsrProviderAdapter):
    provider_id = "whisper"

    def __init__(self) -> None:
        self._backend: WhisperAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._stream_chunks: list[bytes] = []
        self._stream_language = "en-US"
        self._stream_sample_rate = 16000
        self._empty_transcript_rms_threshold = 100
        self._stream_session_id = "stream"
        self._stream_request_id = "stream"
        self._stream_started_at = 0.0

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        del credentials_ref
        self._backend = WhisperAsrBackend(config=config)
        self._empty_transcript_rms_threshold = int(config.get("empty_transcript_rms_threshold", 100) or 100)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._backend is None:
            return ["Provider is not initialized"]
        return []

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            streaming_mode="simulated",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=False,
            supports_confidence=True,
            supports_language_auto_detect=True,
            supports_cpu=True,
            supports_gpu=True,
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
            raise RuntimeError("WhisperProvider is not initialized")
        request = AsrRequest(
            wav_path=audio.wav_path or None,
            audio_bytes=audio.audio_bytes or None,
            language=audio.language,
            enable_word_timestamps=audio.enable_word_timestamps,
            sample_rate=audio.sample_rate_hz,
            metadata={
                **audio.metadata,
                "channels": int(audio.metadata.get("channels", 1) or 1),
                "sample_width_bytes": int(audio.metadata.get("sample_width_bytes", 2) or 2),
            },
        )
        response = self._backend.recognize_once(request)
        result = _normalize(self.provider_id, audio, response, is_partial=False)
        if response.success and not str(response.text or "").strip() and self._has_non_silent_audio(audio):
            result.degraded = True
            result.error_code = "empty_transcript"
            result.error_message = "Whisper returned an empty transcript for non-silent audio"
            result.tags.append("empty_transcript")
            result.raw_metadata_ref = "provider:whisper_empty"
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="ready" if not result.error_code else "degraded",
            message=(
                "recognize_once completed"
                if not result.error_code
                else "recognize_once completed with degraded result"
            ),
            health="ok" if not result.error_code else "degraded",
            error_code=result.error_code,
            error_message=result.error_message,
        )
        return result

    def _has_non_silent_audio(self, audio: ProviderAudio) -> bool:
        threshold = max(self._empty_transcript_rms_threshold, 1)
        if audio.wav_path:
            try:
                with wave.open(audio.wav_path, "rb") as wf:
                    frames = wf.readframes(wf.getframerate() * min(3, max(1, wf.getnchannels())))
                    if frames:
                        return audioop.rms(frames, wf.getsampwidth()) >= threshold
            except Exception:
                return bool(audio.audio_bytes)
            return False
        if audio.audio_bytes:
            try:
                return audioop.rms(audio.audio_bytes, 2) >= threshold
            except Exception:
                return True
        return False

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        opts = options or {}
        self._stream_chunks = []
        self._stream_language = str(opts.get("language", "en-US"))
        self._stream_sample_rate = int(opts.get("sample_rate_hz", 16000))
        self._stream_session_id = str(opts.get("session_id", "stream") or "stream")
        self._stream_request_id = str(opts.get("request_id", "stream") or "stream")
        self._stream_started_at = time.perf_counter()
        self._status = ProviderStatus(provider_id=self.provider_id, state="streaming")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        self._stream_chunks.append(chunk)
        return None

    def stop_stream(self) -> NormalizedAsrResult:
        if self._backend is None:
            raise RuntimeError("WhisperProvider is not initialized")
        response = self._backend.streaming_recognize(
            self._stream_chunks,
            language=self._stream_language,
            sample_rate=self._stream_sample_rate,
        )
        audio = ProviderAudio(
            session_id=self._stream_session_id,
            request_id=self._stream_request_id,
            language=self._stream_language,
            sample_rate_hz=self._stream_sample_rate,
            metadata={"channels": 1, "sample_width_bytes": 2},
        )
        result = _normalize(self.provider_id, audio, response, is_partial=False)
        elapsed_ms = (time.perf_counter() - self._stream_started_at) * 1000.0 if self._stream_started_at else 0.0
        result.latency.total_ms = max(float(result.latency.total_ms), float(elapsed_ms))
        if response.success and not str(response.text or "").strip() and any(self._stream_chunks):
            result.degraded = True
            result.error_code = "empty_transcript"
            result.error_message = "Whisper returned an empty transcript for non-silent streamed audio"
            result.tags.append("empty_transcript")
            result.raw_metadata_ref = "provider:whisper_empty"
        self._stream_chunks = []
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="ready" if not result.error_code else "degraded",
            health="ok" if not result.error_code else "degraded",
            error_code=result.error_code,
            error_message=result.error_message,
        )
        return result

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
