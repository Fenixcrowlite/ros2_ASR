"""AWS cloud provider adapter."""

from __future__ import annotations

from typing import Any

from asr_backend_aws.backend import AwsAsrBackend
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
        words=words,
        confidence=float(response.confidence),
        confidence_available=response.confidence > 0,
        timestamps_available=bool(words),
        language=response.language,
        latency=LatencyMetadata(total_ms=float(response.timings.total_ms)),
        degraded=not response.success,
        error_code=response.error_code,
        error_message=response.error_message,
        tags=["cloud"],
    )


class AwsProvider(AsrProviderAdapter):
    provider_id = "aws"

    def __init__(self) -> None:
        self._backend: AwsAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        merged = dict(config)
        for key in (
            "AWS_PROFILE",
            "AWS_REGION",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_CONFIG_FILE",
            "AWS_SHARED_CREDENTIALS_FILE",
        ):
            if credentials_ref.get(key):
                lowered = key.lower().replace("aws_", "")
                merged[lowered] = credentials_ref[key]
        self._backend = AwsAsrBackend(config=merged)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._backend is None:
            return ["Provider is not initialized"]
        errors: list[str] = []
        if not self._backend.region:
            errors.append("AWS region is missing")
        if not self._backend.s3_bucket:
            errors.append("AWS s3_bucket is missing")
        if not self._backend.has_credentials():
            errors.append(
                "AWS credentials are missing. Provide AWS_PROFILE or AWS access keys."
            )
        errors.extend(self._backend.auth_validation_errors())
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
            raise RuntimeError("AwsProvider is not initialized")
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
        del options
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="unsupported",
            message="AWS streaming is not implemented in this baseline",
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
            error_message="AWS streaming is not implemented in this baseline",
        )

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
