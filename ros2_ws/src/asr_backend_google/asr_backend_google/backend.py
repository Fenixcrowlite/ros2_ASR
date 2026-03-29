"""Google Cloud Speech-to-Text backend with native streaming support."""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Any, Iterable

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
from asr_core.config import as_bool, env_or
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp
from asr_core.streaming import StreamAccumulator


class GoogleStreamingSession:
    """Native Google streaming session backed by SpeechClient.streaming_recognize."""

    def __init__(
        self,
        *,
        client: Any,
        speech_module: Any,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
        model: str = "default",
        region: str = "global",
        enable_word_timestamps: bool = True,
        interim_results: bool = True,
        single_utterance: bool = False,
        enable_voice_activity_events: bool = False,
    ) -> None:
        self._client = client
        self._speech = speech_module
        self._language = normalize_language_code(language, fallback="en-US")
        self._sample_rate = int(sample_rate or 16000)
        self._channels = int(channels or 1)
        self._sample_width_bytes = int(sample_width_bytes or 2)
        self._audio_queue: queue.Queue[bytes | None] = queue.Queue()
        self._done = threading.Event()
        self._accumulator = StreamAccumulator(
            provider="google",
            language=self._language,
            model=str(model or "default"),
            region=str(region or "global"),
        )
        self._config = speech_module.StreamingRecognitionConfig(
            config=speech_module.RecognitionConfig(
                encoding=speech_module.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self._sample_rate,
                language_code=self._language,
                enable_word_time_offsets=bool(enable_word_timestamps),
                model=str(model or "default"),
                audio_channel_count=self._channels,
            ),
            interim_results=bool(interim_results),
            single_utterance=bool(single_utterance),
            enable_voice_activity_events=bool(enable_voice_activity_events),
        )
        self._thread = threading.Thread(target=self._run, name="google-stream-session", daemon=True)
        self._thread.start()

    @staticmethod
    def _classify_error(exc: Exception) -> tuple[str, str]:
        message = str(exc).strip() or exc.__class__.__name__
        lowered = message.lower()
        if "permission denied" in lowered or "permissiondenied" in lowered:
            return "google_access_denied", message
        if "credentials" in lowered:
            return "credential_missing", message
        if "deadline exceeded" in lowered:
            return "timeout", message
        return "google_stream_runtime_error", message

    def _request_iterator(self):
        while True:
            chunk = self._audio_queue.get()
            if chunk is None:
                break
            yield self._speech.StreamingRecognizeRequest(audio_content=bytes(chunk))

    def _run(self) -> None:
        try:
            responses = self._client.streaming_recognize(
                config=self._config,
                requests=self._request_iterator(),
            )
            for response in responses:
                for result in getattr(response, "results", []):
                    if not getattr(result, "alternatives", None):
                        continue
                    alt = result.alternatives[0]
                    text = str(getattr(alt, "transcript", "") or "").strip()
                    confidence = float(getattr(alt, "confidence", 0.0) or 0.0)
                    if not text:
                        continue
                    if bool(getattr(result, "is_final", False)):
                        words: list[WordTimestamp] = []
                        for word_info in getattr(alt, "words", []):
                            words.append(
                                WordTimestamp(
                                    word=str(word_info.word),
                                    start_sec=float(word_info.start_time.total_seconds()),
                                    end_sec=float(word_info.end_time.total_seconds()),
                                    confidence=0.0,
                                )
                            )
                        self._accumulator.add_final(
                            text,
                            words=words,
                            confidence=confidence,
                            language=self._language,
                            backend_info={"model": self._accumulator.model, "region": self._accumulator.region},
                            raw_response=response,
                        )
                    else:
                        self._accumulator.mark_partial(
                            text,
                            confidence=confidence,
                            language=self._language,
                            backend_info={"model": self._accumulator.model, "region": self._accumulator.region},
                            raw_response=response,
                        )
        except Exception as exc:
            error_code, error_message = self._classify_error(exc)
            self._accumulator.set_error(error_code, error_message, raw_response=exc)
        finally:
            self._done.set()

    def push_audio(self, chunk: bytes) -> None:
        self._accumulator.audio_duration_sec += pcm_duration_sec(
            chunk,
            sample_rate=self._sample_rate,
            channels=self._channels,
            sample_width=self._sample_width_bytes,
        )
        self._audio_queue.put(bytes(chunk))

    def drain_partials(self) -> list[AsrResponse]:
        return self._accumulator.drain_partials()

    def stop(self) -> AsrResponse:
        self._accumulator.note_stop_requested()
        self._audio_queue.put(None)
        self._done.wait(timeout=20.0)
        self._thread.join(timeout=1.0)
        return self._accumulator.build_final_response()


@register_backend("google")
class GoogleAsrBackend(AsrBackend):
    """Google Speech backend with config/ENV-based credentials."""

    name = "google"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=True,
            streaming_mode="native",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=True,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
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
        self.streaming_interim_results = as_bool(
            env_or(self.config, "streaming_interim_results", "ASR_GOOGLE_STREAMING_INTERIM_RESULTS", "true"),
            default=True,
        )
        self.streaming_single_utterance = as_bool(
            env_or(self.config, "streaming_single_utterance", "ASR_GOOGLE_STREAMING_SINGLE_UTTERANCE", "false"),
            default=False,
        )
        self.streaming_voice_activity_events = as_bool(
            env_or(self.config, "streaming_voice_activity_events", "ASR_GOOGLE_STREAMING_VAD_EVENTS", "false"),
            default=False,
        )
        self._speech: Any = None
        self._client: Any = client

    def has_credentials(self) -> bool:
        return bool(self.credentials) and Path(self.credentials).exists()

    def _load_client(self) -> bool:
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
        return self._speech.RecognitionConfig(
            encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language,
            enable_word_time_offsets=enable_word_timestamps,
            model=model,
        )

    @staticmethod
    def _is_unsupported_model_error(error_message: str) -> bool:
        text = str(error_message or "").lower()
        return (
            "incorrect model specified" in text
            or "model is currently not supported for language" in text
            or "requested model is currently not supported" in text
        )

    def create_stream_session(
        self,
        *,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
        enable_word_timestamps: bool = True,
    ) -> GoogleStreamingSession:
        if not self.credentials:
            raise RuntimeError(
                "Missing Google credentials. Set GOOGLE_APPLICATION_CREDENTIALS or backends.google.credentials_json."
            )
        if not Path(self.credentials).exists():
            raise RuntimeError(f"Google credentials file not found: {self.credentials}")
        if not self._load_client():
            raise RuntimeError("Unable to initialize google-cloud-speech client")
        return GoogleStreamingSession(
            client=self._client,
            speech_module=self._speech,
            language=language,
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width_bytes,
            model=self.model,
            region=self.region,
            enable_word_timestamps=enable_word_timestamps,
            interim_results=self.streaming_interim_results,
            single_utterance=self.streaming_single_utterance,
            enable_voice_activity_events=self.streaming_voice_activity_events,
        )

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
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
            config = self._build_recognition_config(
                sample_rate=sample_rate,
                language=language,
                enable_word_timestamps=bool(request.enable_word_timestamps),
                model=requested_model,
            )
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
            post_ms = (time.perf_counter() - post_start) * 1000.0
            backend_info = {
                "provider": "google",
                "model": requested_model,
                "region": self.region,
            }

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
            error_message = str(exc)
            error_code = "google_runtime_error"
            if self._is_unsupported_model_error(error_message):
                error_code = "google_model_unsupported"
                error_message = (
                    f"Google model '{self.model}' is not supported for language '{language}'. "
                    f"{error_message}"
                )
            return AsrResponse(
                success=False,
                error_code=error_code,
                error_message=error_message,
                backend_info={"provider": "google", "model": self.model, "region": self.region},
                language=language,
            )

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        session = self.create_stream_session(language=language, sample_rate=sample_rate)
        for chunk in chunks:
            session.push_audio(bytes(chunk))
        return session.stop()
