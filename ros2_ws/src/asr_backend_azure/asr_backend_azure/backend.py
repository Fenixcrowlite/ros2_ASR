"""Azure Cognitive Services Speech backend (recognize-once)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from asr_core.audio import audio_bytes_to_temp_wav, sample_width_from_encoding, wav_duration_sec
from asr_core.backend import AsrBackend
from asr_core.config import env_or
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp


@register_backend("azure")
class AzureAsrBackend(AsrBackend):
    """Azure Speech SDK integration with normalized output fields."""

    name = "azure"

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
        """Read key/region/endpoint and lazy SDK handle."""
        super().__init__(config=config, client=client)
        self.key = env_or(self.config, "speech_key", "AZURE_SPEECH_KEY", "")
        self.region = env_or(self.config, "region", "AZURE_SPEECH_REGION", "")
        self.endpoint = env_or(self.config, "endpoint", "ASR_AZURE_ENDPOINT", "")
        self._speechsdk: Any = client

    def has_credentials(self) -> bool:
        """Azure requires both key and region."""
        return bool(self.key and self.region)

    def _load_sdk(self) -> bool:
        """Import Azure Speech SDK once."""
        if self._speechsdk is not None:
            return True
        try:
            import azure.cognitiveservices.speech as speechsdk

            self._speechsdk = speechsdk
            return True
        except Exception:
            return False

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
        """Convert request to local WAV path, returning `(path, cleanup_needed)`."""
        if request.wav_path:
            return request.wav_path, False
        if request.audio_bytes:
            return (
                audio_bytes_to_temp_wav(
                    request.audio_bytes,
                    sample_rate=int(request.sample_rate or 16000),
                    channels=int(request.metadata.get("channels", 1) or 1),
                    sample_width=int(
                        request.metadata.get(
                            "sample_width_bytes",
                            sample_width_from_encoding(request.metadata.get("encoding"), default=2),
                        )
                        or 2
                    ),
                    prefix="azure_audio_",
                ),
                True,
            )
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Run one-shot Azure recognition and parse detailed JSON output."""
        preprocess_start = time.perf_counter()
        language = normalize_language_code(request.language, fallback="en-US")
        if not self.key:
            return AsrResponse(
                success=False,
                error_code="credential_missing",
                error_message=(
                    "Missing Azure key. Set AZURE_SPEECH_KEY or backends.azure.speech_key."
                ),
                backend_info={"provider": "azure", "model": "speech", "region": self.region},
                language=language,
            )
        if not self.region:
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message=(
                    "Missing Azure region. Set AZURE_SPEECH_REGION or backends.azure.region."
                ),
                backend_info={"provider": "azure", "model": "speech", "region": ""},
                language=language,
            )
        if not self._load_sdk():
            return AsrResponse(
                success=False,
                error_code="client_init_error",
                error_message="Unable to initialize Azure speech SDK",
                backend_info={"provider": "azure", "model": "speech", "region": self.region},
                language=language,
            )

        tmp_file: str | None = None
        try:
            wav_path, cleanup = self._request_to_wav_path(request)
            if cleanup:
                tmp_file = wav_path
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0

            speech_config = self._speechsdk.SpeechConfig(subscription=self.key, region=self.region)
            if self.endpoint:
                speech_config.endpoint_id = self.endpoint
            speech_config.speech_recognition_language = language or "en-US"
            speech_config.output_format = self._speechsdk.OutputFormat.Detailed
            speech_config.request_word_level_timestamps()

            audio_config = self._speechsdk.audio.AudioConfig(filename=wav_path)
            recognizer = self._speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )

            inf_start = time.perf_counter()
            result = recognizer.recognize_once_async().get()
            inference_ms = (time.perf_counter() - inf_start) * 1000.0

            if result.reason == self._speechsdk.ResultReason.NoMatch:
                return AsrResponse(
                    success=False,
                    error_code="no_match",
                    error_message="Azure returned no match",
                    backend_info={"provider": "azure", "model": "speech", "region": self.region},
                    language=language,
                )
            if result.reason == self._speechsdk.ResultReason.Canceled:
                details = self._speechsdk.CancellationDetails.from_result(result)
                return AsrResponse(
                    success=False,
                    error_code="azure_canceled",
                    error_message=details.error_details,
                    backend_info={"provider": "azure", "model": "speech", "region": self.region},
                    language=language,
                )

            detailed_json = result.properties.get(
                self._speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
                "{}",
            )
            parsed = json.loads(detailed_json)
            nbest = parsed.get("NBest", [])
            top = nbest[0] if nbest else {}
            confidence = float(top.get("Confidence", 0.0))
            words: list[WordTimestamp] = []
            for item in top.get("Words", []):
                offset_sec = float(item.get("Offset", 0)) / 10_000_000.0
                dur_sec = float(item.get("Duration", 0)) / 10_000_000.0
                words.append(
                    WordTimestamp(
                        word=item.get("Word", ""),
                        start_sec=offset_sec,
                        end_sec=offset_sec + dur_sec,
                        confidence=float(item.get("Confidence", confidence)),
                    )
                )

            post_start = time.perf_counter()
            duration = wav_duration_sec(wav_path)
            post_ms = (time.perf_counter() - post_start) * 1000.0
            return AsrResponse(
                text=result.text.strip(),
                partials=[],
                confidence=confidence,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=language,
                backend_info={"provider": "azure", "model": "speech", "region": self.region},
                timings=AsrTimings(
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=post_ms,
                ),
                audio_duration_sec=duration,
                success=True,
            )
        except Exception as exc:
            return AsrResponse(
                success=False,
                error_code="azure_runtime_error",
                error_message=str(exc),
                backend_info={"provider": "azure", "model": "speech", "region": self.region},
                language=language,
            )
        finally:
            if tmp_file and Path(tmp_file).exists():
                Path(tmp_file).unlink(missing_ok=True)
