"""Azure cloud provider adapter with native streaming."""

from __future__ import annotations

from typing import Any

from asr_backend_azure.backend import AzureAsrBackend, AzureStreamingSession
from asr_core.models import AsrRequest, AsrResponse
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus


def _metadata_float(response: AsrResponse, key: str) -> float:
    backend_info = getattr(response, "backend_info", {}) or {}
    value = backend_info.get(key, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize(provider_id: str, audio: ProviderAudio, response: AsrResponse, *, is_partial: bool = False) -> NormalizedAsrResult:
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
    text = str(response.text or "").strip()
    degraded = not response.success
    error_code = response.error_code
    error_message = response.error_message
    if not is_partial and not degraded and not text:
        degraded = True
        error_code = error_code or "empty_transcript"
        error_message = error_message or "Azure returned an empty transcript."

    backend_info = getattr(response, "backend_info", {}) or {}
    return NormalizedAsrResult(
        request_id=audio.request_id,
        session_id=audio.session_id,
        provider_id=provider_id,
        text=text,
        is_final=not is_partial,
        is_partial=is_partial,
        utterance_start_sec=words[0].start_sec if words else 0.0,
        utterance_end_sec=words[-1].end_sec if words else 0.0,
        words=words,
        confidence=float(response.confidence),
        confidence_available=float(response.confidence) > 0.0,
        timestamps_available=bool(words),
        language=response.language or audio.language,
        language_detected=False,
        latency=LatencyMetadata(
            total_ms=float(response.timings.total_ms),
            first_partial_ms=float(_metadata_float(response, "first_partial_ms")),
            finalization_ms=float(_metadata_float(response, "finalization_ms")),
        ),
        raw_metadata_ref="",
        degraded=degraded,
        error_code=error_code,
        error_message=error_message,
        tags=["cloud", "native_stream"] if is_partial or backend_info.get("streaming_mode") == "native" else ["cloud"],
    )


class AzureProvider(AsrProviderAdapter):
    provider_id = "azure"

    def __init__(self) -> None:
        self._backend: AzureAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._stream_session: AzureStreamingSession | None = None
        self._stream_audio = ProviderAudio(
            session_id="stream",
            request_id="stream",
            language="en-US",
            sample_rate_hz=16000,
        )

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        merged = dict(config)
        if "AZURE_SPEECH_KEY" in credentials_ref:
            merged["speech_key"] = credentials_ref["AZURE_SPEECH_KEY"]
        if "AZURE_SPEECH_REGION" in credentials_ref and not merged.get("region"):
            merged["region"] = credentials_ref["AZURE_SPEECH_REGION"]
        if "ASR_AZURE_ENDPOINT" in credentials_ref and not merged.get("endpoint"):
            merged["endpoint"] = credentials_ref["ASR_AZURE_ENDPOINT"]
        self._backend = AzureAsrBackend(config=merged)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if self._backend is None:
            return ["Provider is not initialized"]
        if not self._backend.key:
            errors.append("Azure speech key is missing. Provide AZURE_SPEECH_KEY.")
        if not self._backend.region:
            errors.append("Azure region is missing. Provide AZURE_SPEECH_REGION.")
        return errors

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            streaming_mode="native",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=True,
            supports_confidence=True,
            supports_language_auto_detect=False,
            supports_cpu=True,
            supports_gpu=False,
            requires_network=True,
            cost_model_type="cloud_per_minute",
        )

    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        del options
        if self._backend is None:
            raise RuntimeError("AzureProvider is not initialized")
        request = AsrRequest(
            wav_path=audio.wav_path or None,
            audio_bytes=audio.audio_bytes or None,
            language=audio.language,
            enable_word_timestamps=audio.enable_word_timestamps,
            sample_rate=audio.sample_rate_hz,
            metadata=audio.metadata,
        )
        response = self._backend.recognize_once(request)
        result = _normalize(self.provider_id, audio, response)
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="ready" if response.success else "error",
            message="recognize_once completed",
            health="ok" if response.success else "degraded",
            error_code=response.error_code,
            error_message=response.error_message,
        )
        return result

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        opts = options or {}
        if self._backend is None:
            raise RuntimeError("AzureProvider is not initialized")
        self._stream_audio = ProviderAudio(
            session_id=str(opts.get("session_id", "stream") or "stream"),
            request_id=str(opts.get("request_id", "stream") or "stream"),
            language=str(opts.get("language", "en-US") or "en-US"),
            sample_rate_hz=int(opts.get("sample_rate_hz", 16000) or 16000),
            enable_word_timestamps=True,
            metadata={
                "channels": int(opts.get("channels", 1) or 1),
                "encoding": str(opts.get("encoding", "pcm_s16le") or "pcm_s16le"),
                "sample_width_bytes": int(opts.get("sample_width_bytes", 2) or 2),
            },
        )
        self._stream_session = self._backend.create_stream_session(
            language=self._stream_audio.language,
            sample_rate=self._stream_audio.sample_rate_hz,
            channels=int(self._stream_audio.metadata.get("channels", 1) or 1),
            sample_width_bytes=int(self._stream_audio.metadata.get("sample_width_bytes", 2) or 2),
        )
        self._status = ProviderStatus(provider_id=self.provider_id, state="streaming")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        if self._stream_session is None:
            raise RuntimeError("Azure stream is not active")
        self._stream_session.push_audio(chunk)
        return None

    def drain_stream_results(self) -> list[NormalizedAsrResult]:
        if self._stream_session is None:
            return []
        return [
            _normalize(self.provider_id, self._stream_audio, item, is_partial=True)
            for item in self._stream_session.drain_partials()
        ]

    def stop_stream(self) -> NormalizedAsrResult:
        if self._stream_session is None:
            raise RuntimeError("Azure stream is not active")
        response = self._stream_session.stop()
        result = _normalize(self.provider_id, self._stream_audio, response)
        self._stream_session = None
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="ready" if not result.error_code else "degraded",
            message="streaming completed",
            health="ok" if not result.error_code else "degraded",
            error_code=result.error_code,
            error_message=result.error_message,
        )
        return result

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._stream_session = None
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
