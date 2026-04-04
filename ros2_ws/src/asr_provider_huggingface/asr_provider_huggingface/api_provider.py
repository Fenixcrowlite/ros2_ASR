"""Hugging Face ASR provider using the hosted Inference API over HTTP."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio
from asr_provider_huggingface.common import (
    BaseHuggingFaceProvider,
    api_return_timestamps,
    build_transcription_result,
    provider_audio_to_wav_bytes,
    resolve_token,
)
from asr_provider_huggingface.http_client import (
    HuggingFaceInferenceError,
    HuggingFaceInferenceHttpClient,
)


class HuggingFaceAPIProvider(BaseHuggingFaceProvider):
    provider_id = "huggingface_api"
    display_name = "Hugging Face API"
    implementation = "requests"
    source = "api"

    def __init__(self) -> None:
        super().__init__()
        self._token = ""
        self._client: HuggingFaceInferenceHttpClient | None = None

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        self._config = dict(config)
        self._token = resolve_token(credentials_ref)
        timeout_sec = float(self._config.get("timeout_sec", 60.0) or 60.0)
        self._client = HuggingFaceInferenceHttpClient(
            token=self._token,
            timeout_sec=timeout_sec,
            base_url=str(
                self._config.get("base_url", "https://api-inference.huggingface.co/models/{model}")
                or "https://api-inference.huggingface.co/models/{model}"
            ),
        )
        self._set_metadata(
            model_id=str(self._config.get("model_id", "") or ""),
            endpoint=str(self._config.get("endpoint_url", "") or self._config.get("base_url", "")),
        )
        self._status = self.get_status().__class__(
            provider_id=self.provider_id,
            state="initialized",
            message="initialized",
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not str(self._config.get("model_id", "") or "").strip():
            errors.append("Hugging Face API model_id is required.")
        if not self._token:
            errors.append("HF_TOKEN is required for Hugging Face API mode.")
        return errors

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            streaming_mode="none",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=False,
            supports_confidence=False,
            supports_language_auto_detect=False,
            supports_cpu=True,
            supports_gpu=False,
            requires_network=True,
            cost_model_type="cloud_per_request",
        )

    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        del options
        if self._client is None:
            self._record_exception(
                error_code="hf_api_uninitialized",
                error_message="Hugging Face API client is not initialized.",
            )
            return NormalizedAsrResult(
                request_id=audio.request_id,
                session_id=audio.session_id,
                provider_id=self.provider_id,
                text="",
                is_final=True,
                is_partial=False,
                language=audio.language,
                latency=LatencyMetadata(),
                degraded=True,
                error_code="hf_api_uninitialized",
                error_message="Hugging Face API client is not initialized.",
                tags=["hf_api"],
            )

        try:
            preprocess_started = perf_counter()
            wav_bytes = provider_audio_to_wav_bytes(audio)
            preprocess_ms = (perf_counter() - preprocess_started) * 1000.0

            inference_started = perf_counter()
            payload = self._client.automatic_speech_recognition(
                audio_bytes=wav_bytes,
                model_id=str(self._config.get("model_id", "") or ""),
                endpoint_url=str(self._config.get("endpoint_url", "") or ""),
                return_timestamps=api_return_timestamps(
                    self._config,
                    enable_word_timestamps=audio.enable_word_timestamps,
                ),
                generation_parameters=dict(
                    self._config.get("generation_parameters", {}) or {}
                ),
            )
            inference_ms = (perf_counter() - inference_started) * 1000.0

            postprocess_started = perf_counter()
            result = build_transcription_result(
                provider_id=self.provider_id,
                audio=audio,
                payload=payload,
                latency=LatencyMetadata(
                    total_ms=0.0,
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=0.0,
                ),
                language=audio.language,
                tags=["hf_api", "http"],
            )
            result.latency.postprocess_ms = (perf_counter() - postprocess_started) * 1000.0
            result.latency.total_ms = (
                result.latency.preprocess_ms
                + result.latency.inference_ms
                + result.latency.postprocess_ms
            )
            self._record_result(result)
            return result
        except HuggingFaceInferenceError as exc:
            self._record_exception(error_code=exc.code, error_message=exc.message)
            return NormalizedAsrResult(
                request_id=audio.request_id,
                session_id=audio.session_id,
                provider_id=self.provider_id,
                text="",
                is_final=True,
                is_partial=False,
                language=audio.language,
                latency=LatencyMetadata(),
                degraded=True,
                error_code=exc.code,
                error_message=exc.message,
                tags=["hf_api", "http"],
            )
        except Exception as exc:
            error_message = str(exc)
            self._record_exception(
                error_code="hf_api_runtime_error",
                error_message=error_message,
            )
            return NormalizedAsrResult(
                request_id=audio.request_id,
                session_id=audio.session_id,
                provider_id=self.provider_id,
                text="",
                is_final=True,
                is_partial=False,
                language=audio.language,
                latency=LatencyMetadata(),
                degraded=True,
                error_code="hf_api_runtime_error",
                error_message=error_message,
                tags=["hf_api", "http"],
            )

    def teardown(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        super().teardown()
