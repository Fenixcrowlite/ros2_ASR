"""Google Cloud Speech-to-Text backend (recognize-once)."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from asr_core.audio import (
    pcm_duration_sec,
    sample_width_from_encoding,
    wav_bytes_to_pcm,
    wav_duration_bytes,
    wav_duration_sec,
    wav_info,
    wav_info_bytes,
)
from asr_core.backend import AsrBackend
from asr_core.config import env_or
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp


@register_backend("google")
class GoogleAsrBackend(AsrBackend):
    """Google Speech backend with config/ENV-based credentials."""

    name = "google"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=False,
            streaming_mode="simulated",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=True,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        """Read model/region/endpoint/credentials and lazy client handle."""
        super().__init__(config=config, client=client)
        self.model = env_or(self.config, "model", "ASR_GOOGLE_MODEL", "latest_long")
        self.region = env_or(self.config, "region", "ASR_GOOGLE_REGION", "global")
        self.endpoint = env_or(self.config, "endpoint", "ASR_GOOGLE_ENDPOINT", "")
        self.credentials = env_or(
            self.config,
            "credentials_json",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "",
        )
        self.project_id = env_or(self.config, "project_id", "GOOGLE_CLOUD_PROJECT", "")
        self._speech: Any = None
        self._client: Any = client

    def has_credentials(self) -> bool:
        """Check that credential file path exists."""
        return bool(self.credentials) and Path(self.credentials).exists()

    def _load_client(self) -> bool:
        """Initialize google client once (with optional endpoint override)."""
        if self._client is not None:
            return True
        try:
            from google.cloud import speech

            self._speech = speech
            client_options = {"api_endpoint": self.endpoint} if self.endpoint else None
            if self.credentials and Path(self.credentials).exists():
                if client_options:
                    self._client = speech.SpeechClient.from_service_account_file(
                        self.credentials,
                        client_options=client_options,
                    )
                else:
                    self._client = speech.SpeechClient.from_service_account_file(self.credentials)
            else:
                if client_options:
                    self._client = speech.SpeechClient(client_options=client_options)
                else:
                    self._client = speech.SpeechClient()
            return True
        except Exception:
            return False

    def _request_audio(self, request: AsrRequest) -> tuple[bytes, int, float]:
        """Return `(pcm_audio_bytes, sample_rate_hz, duration_sec)`."""
        if request.wav_path:
            wav_bytes = Path(request.wav_path).read_bytes()
            sample_rate, _, _, _ = wav_info(request.wav_path)
            return wav_bytes_to_pcm(wav_bytes), sample_rate, wav_duration_sec(request.wav_path)
        if request.audio_bytes:
            if request.audio_bytes[:4] == b"RIFF":
                sample_rate, _, _, _ = wav_info_bytes(request.audio_bytes)
                return (
                    wav_bytes_to_pcm(request.audio_bytes),
                    sample_rate,
                    wav_duration_bytes(request.audio_bytes),
                )
            channels = int(request.metadata.get("channels", 1) or 1)
            sample_width = int(
                request.metadata.get(
                    "sample_width_bytes",
                    sample_width_from_encoding(request.metadata.get("encoding"), default=2),
                )
                or 2
            )
            sample_rate = int(request.sample_rate or 16000)
            return (
                request.audio_bytes,
                sample_rate,
                pcm_duration_sec(
                    request.audio_bytes,
                    sample_rate=sample_rate,
                    channels=channels,
                    sample_width=sample_width,
                ),
            )
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def _build_recognition_config(
        self,
        *,
        sample_rate: int,
        language: str,
        enable_word_timestamps: bool,
        model: str,
    ):
        """Build Google RecognitionConfig object for one request."""
        return self._speech.RecognitionConfig(
            encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language,
            enable_word_time_offsets=enable_word_timestamps,
            model=model,
        )

    @staticmethod
    def _supports_default_model_fallback(error_message: str) -> bool:
        """Detect model-level request errors where `default` fallback is useful."""
        text = str(error_message or "").lower()
        return (
            "incorrect model specified" in text
            or "model is currently not supported for language" in text
            or "requested model is currently not supported" in text
        )

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Run one-shot Google recognition and normalize fields."""
        preprocess_start = time.perf_counter()
        language = normalize_language_code(request.language, fallback="en-US")
        if not self.credentials:
            return AsrResponse(
                success=False,
                error_code="credential_missing",
                error_message=(
                    "Missing Google credentials. Set GOOGLE_APPLICATION_CREDENTIALS or "
                    "backends.google.credentials_json."
                ),
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=language,
            )
        if not Path(self.credentials).exists():
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message=f"Google credentials file not found: {self.credentials}",
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=language,
            )
        if not self._load_client():
            return AsrResponse(
                success=False,
                error_code="client_init_error",
                error_message="Unable to initialize google-cloud-speech client",
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=language,
            )

        try:
            audio_bytes, sample_rate, duration = self._request_audio(request)
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0
            audio = self._speech.RecognitionAudio(content=audio_bytes)
            requested_model = str(self.model)
            effective_model = requested_model
            config = self._build_recognition_config(
                sample_rate=sample_rate,
                language=language,
                enable_word_timestamps=bool(request.enable_word_timestamps),
                model=effective_model,
            )
            inf_start = time.perf_counter()
            try:
                response = self._client.recognize(config=config, audio=audio)
            except Exception as primary_exc:
                if (
                    effective_model != "default"
                    and self._supports_default_model_fallback(str(primary_exc))
                ):
                    fallback_config = self._build_recognition_config(
                        sample_rate=sample_rate,
                        language=language,
                        enable_word_timestamps=bool(request.enable_word_timestamps),
                        model="default",
                    )
                    response = self._client.recognize(config=fallback_config, audio=audio)
                    effective_model = "default"
                else:
                    raise
            inference_ms = (time.perf_counter() - inf_start) * 1000.0

            text_parts: list[str] = []
            confidences: list[float] = []
            words: list[WordTimestamp] = []
            for result in response.results:
                if not result.alternatives:
                    continue
                alt = result.alternatives[0]
                text_parts.append(alt.transcript.strip())
                if hasattr(alt, "confidence"):
                    confidences.append(float(alt.confidence))
                for word_info in getattr(alt, "words", []):
                    start_sec = float(word_info.start_time.total_seconds())
                    end_sec = float(word_info.end_time.total_seconds())
                    words.append(
                        WordTimestamp(
                            word=str(word_info.word),
                            start_sec=start_sec,
                            end_sec=end_sec,
                            confidence=0.0,
                        )
                    )
            text = " ".join([t for t in text_parts if t]).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            post_start = time.perf_counter()
            post_ms = (time.perf_counter() - post_start) * 1000.0
            backend_info = {
                "provider": "google",
                "model": effective_model,
                "region": self.region,
            }
            if effective_model != requested_model:
                backend_info["requested_model"] = requested_model

            return AsrResponse(
                text=text,
                partials=[],
                confidence=avg_conf,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=language,
                backend_info=backend_info,
                timings=AsrTimings(
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=post_ms,
                ),
                audio_duration_sec=duration,
                success=True,
                raw_response=response,
            )
        except Exception as exc:
            return AsrResponse(
                success=False,
                error_code="google_runtime_error",
                error_message=str(exc),
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=language,
            )
