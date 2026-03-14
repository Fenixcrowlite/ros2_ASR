"""Azure cloud provider adapter (cloud baseline)."""

from __future__ import annotations

from typing import Any

from asr_backend_azure.backend import AzureAsrBackend
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
        tags=["cloud"],
    )


class AzureProvider(AsrProviderAdapter):
    provider_id = "azure"

    def __init__(self) -> None:
        self._backend: AzureAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")

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
            supports_streaming=False,
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=False,
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
        del options
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="unsupported",
            message="Azure streaming is not implemented in this baseline",
            health="degraded",
        )

    def push_audio(self, chunk: bytes) -> None:
        del chunk

    def stop_stream(self) -> NormalizedAsrResult:
        return NormalizedAsrResult(
            request_id="stream",
            session_id="stream",
            provider_id=self.provider_id,
            text="",
            is_final=True,
            is_partial=False,
            degraded=True,
            error_code="unsupported",
            error_message="Azure streaming is not implemented in this baseline",
        )

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
