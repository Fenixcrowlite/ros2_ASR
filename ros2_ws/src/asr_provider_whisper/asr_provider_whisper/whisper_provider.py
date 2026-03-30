"""Whisper provider adapter (local baseline)."""

from __future__ import annotations

import wave
from typing import Any

from asr_backend_whisper.backend import WhisperAsrBackend
from asr_core.audio import pcm_rms
from asr_core.models import AsrRequest
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus


def _normalize(
    provider_id: str, audio: ProviderAudio, response: Any, is_partial: bool
) -> NormalizedAsrResult:
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
        audio_duration_sec=float(getattr(response, "audio_duration_sec", 0.0) or 0.0),
        words=words,
        confidence=float(response.confidence),
        confidence_available=response.confidence > 0,
        timestamps_available=bool(words),
        language=response.language,
        language_detected=False,
        latency=LatencyMetadata(
            total_ms=float(response.timings.total_ms),
            preprocess_ms=float(response.timings.preprocess_ms),
            inference_ms=float(response.timings.inference_ms),
            postprocess_ms=float(response.timings.postprocess_ms),
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
        self._config: dict[str, Any] = {}
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._empty_transcript_rms_threshold = 100

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        del credentials_ref
        self._config = dict(config)
        self._backend = WhisperAsrBackend(config=config)
        self._empty_transcript_rms_threshold = int(
            config.get("empty_transcript_rms_threshold", 100) or 100
        )
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._backend is None:
            return ["Provider is not initialized"]
        if "allow_cpu_fallback" in self._config:
            return [
                "Whisper setting `allow_cpu_fallback` is no longer supported. "
                "Fix CUDA runtime libraries or set device=cpu explicitly."
            ]
        return []

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            streaming_mode="none",
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
        if (
            response.success
            and not str(response.text or "").strip()
            and self._has_non_silent_audio(audio)
        ):
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
                        return (
                            pcm_rms(
                                frames,
                                sample_width=wf.getsampwidth(),
                                signed=wf.getsampwidth() != 1,
                            )
                            >= threshold
                        )
            except Exception:
                return bool(audio.audio_bytes)
            return False
        if audio.audio_bytes:
            try:
                return pcm_rms(audio.audio_bytes, sample_width=2, signed=True) >= threshold
            except Exception:
                return True
        return False

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        del options
        raise RuntimeError("WhisperProvider does not support provider_stream mode")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        del chunk
        raise RuntimeError("WhisperProvider does not support provider_stream mode")

    def stop_stream(self) -> NormalizedAsrResult:
        raise RuntimeError("WhisperProvider does not support provider_stream mode")

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
