"""Google Cloud Speech-to-Text backend (recognize-once)."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

from asr_core.audio import wav_duration_sec, wav_info
from asr_core.backend import AsrBackend
from asr_core.config import env_or
from asr_core.factory import register_backend
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
            if self.endpoint:
                self._client = speech.SpeechClient(client_options={"api_endpoint": self.endpoint})
            else:
                self._client = speech.SpeechClient()
            return True
        except Exception:
            return False

    def _request_audio(self, request: AsrRequest) -> tuple[bytes, str | None, bool]:
        """Return `(audio_bytes, wav_path_for_metadata, cleanup_tmp)`."""
        if request.wav_path:
            with open(request.wav_path, "rb") as f:
                return f.read(), request.wav_path, False
        if request.audio_bytes:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="google_audio_")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(request.audio_bytes)
            return request.audio_bytes, tmp_path, True
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Run one-shot Google recognition and normalize fields."""
        preprocess_start = time.perf_counter()
        if not self.credentials:
            return AsrResponse(
                success=False,
                error_code="credential_missing",
                error_message=(
                    "Missing Google credentials. Set GOOGLE_APPLICATION_CREDENTIALS or "
                    "backends.google.credentials_json."
                ),
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=request.language,
            )
        if not Path(self.credentials).exists():
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message=f"Google credentials file not found: {self.credentials}",
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=request.language,
            )
        if not self._load_client():
            return AsrResponse(
                success=False,
                error_code="client_init_error",
                error_message="Unable to initialize google-cloud-speech client",
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=request.language,
            )

        tmp_wav: str | None = None
        try:
            audio_bytes, wav_path, cleanup = self._request_audio(request)
            if cleanup:
                tmp_wav = wav_path
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0
            sample_rate = 16000
            if wav_path:
                sample_rate, _, _, _ = wav_info(wav_path)
            config = self._speech.RecognitionConfig(
                encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=request.language,
                enable_word_time_offsets=bool(request.enable_word_timestamps),
                model=self.model,
            )
            audio = self._speech.RecognitionAudio(content=audio_bytes)
            inf_start = time.perf_counter()
            response = self._client.recognize(config=config, audio=audio)
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
            duration = wav_duration_sec(wav_path) if wav_path else 0.0
            post_ms = (time.perf_counter() - post_start) * 1000.0
            return AsrResponse(
                text=text,
                partials=[],
                confidence=avg_conf,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=request.language,
                backend_info={"provider": "google", "model": self.model, "region": self.region},
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
                language=request.language,
            )
        finally:
            if tmp_wav and Path(tmp_wav).exists():
                Path(tmp_wav).unlink(missing_ok=True)
