"""Azure Cognitive Services Speech backend with native streaming support."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Iterable

from asr_core.audio import (
    audio_bytes_to_temp_wav,
    pcm_duration_sec,
    sample_width_from_encoding,
    wav_duration_sec,
)
from asr_core.backend import AsrBackend
from asr_core.config import as_bool, env_or
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp
from asr_core.streaming import StreamAccumulator


def _parse_azure_json(raw_payload: str, *, default_confidence: float = 0.0) -> tuple[float, list[WordTimestamp]]:
    parsed = json.loads(raw_payload or "{}")
    nbest = parsed.get("NBest", [])
    top = nbest[0] if nbest else {}
    confidence = float(top.get("Confidence", default_confidence))
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
    return confidence, words


def _cancellation_details(speechsdk: Any, result: Any) -> Any:
    details_cls = getattr(speechsdk, "CancellationDetails", None)
    if details_cls is None:
        return None


def _is_endpoint_url(value: str) -> bool:
    text = str(value or "").strip().lower()
    return text.startswith("https://") or text.startswith("wss://") or text.startswith("http://")


def _build_speech_config(
    speechsdk: Any,
    *,
    key: str,
    region: str,
    endpoint: str,
    language: str,
) -> Any:
    endpoint_text = str(endpoint or "").strip()
    if endpoint_text and _is_endpoint_url(endpoint_text):
        speech_config = speechsdk.SpeechConfig(subscription=key, endpoint=endpoint_text)
    else:
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        if endpoint_text:
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndpointId,
                endpoint_text,
            )
    speech_config.speech_recognition_language = language or "en-US"
    speech_config.output_format = speechsdk.OutputFormat.Detailed
    speech_config.request_word_level_timestamps()
    return speech_config
    from_result = getattr(details_cls, "from_result", None)
    if callable(from_result):
        return from_result(result)
    try:
        return details_cls(result)
    except Exception:
        return None


class AzureStreamingSession:
    """Native Azure push-stream session using continuous recognition."""

    def __init__(
        self,
        *,
        speechsdk: Any,
        key: str,
        region: str,
        endpoint: str,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
        partial_stability_threshold: int = 3,
    ) -> None:
        self._speechsdk = speechsdk
        self._language = normalize_language_code(language, fallback="en-US")
        self._sample_rate = int(sample_rate or 16000)
        self._channels = int(channels or 1)
        self._sample_width_bytes = int(sample_width_bytes or 2)
        self._stopped = threading.Event()
        self._accumulator = StreamAccumulator(
            provider="azure",
            language=self._language,
            model="speech",
            region=region,
        )

        speech_config = _build_speech_config(
            speechsdk,
            key=key,
            region=region,
            endpoint=endpoint,
            language=self._language,
        )
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold,
            str(max(int(partial_stability_threshold or 3), 1)),
        )

        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=self._sample_rate,
            bits_per_sample=max(self._sample_width_bytes * 8, 16),
            channels=self._channels,
        )
        self._push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self._push_stream)
        self._recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        self._recognizer.recognizing.connect(self._on_recognizing)
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.canceled.connect(self._on_canceled)
        self._recognizer.session_stopped.connect(self._on_session_stopped)

        start_future = self._recognizer.start_continuous_recognition_async()
        if hasattr(start_future, "get"):
            start_future.get()

    def _on_recognizing(self, evt) -> None:
        result = getattr(evt, "result", None)
        if result is None:
            return
        if result.reason != self._speechsdk.ResultReason.RecognizingSpeech:
            return
        text = str(result.text or "").strip()
        if not text:
            return
        self._accumulator.mark_partial(
            text,
            language=self._language,
            backend_info={"model": "speech", "region": self._accumulator.region},
            raw_response=result,
        )

    def _on_recognized(self, evt) -> None:
        result = getattr(evt, "result", None)
        if result is None:
            return
        if result.reason == self._speechsdk.ResultReason.NoMatch:
            return
        if result.reason != self._speechsdk.ResultReason.RecognizedSpeech:
            return

        detailed_json = result.properties.get(
            self._speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
            "{}",
        )
        confidence, words = _parse_azure_json(detailed_json, default_confidence=0.0)
        self._accumulator.add_final(
            str(result.text or "").strip(),
            words=words,
            confidence=confidence,
            language=self._language,
            backend_info={"model": "speech", "region": self._accumulator.region},
            raw_response=result,
        )

    def _on_canceled(self, evt) -> None:
        details = _cancellation_details(self._speechsdk, evt.result)
        self._accumulator.set_error(
            "azure_canceled",
            str(getattr(details, "error_details", "") or "Azure continuous recognition canceled"),
            raw_response=evt.result,
        )
        self._stopped.set()

    def _on_session_stopped(self, evt) -> None:
        del evt
        self._stopped.set()

    def push_audio(self, chunk: bytes) -> None:
        self._accumulator.audio_duration_sec += pcm_duration_sec(
            chunk,
            sample_rate=self._sample_rate,
            channels=self._channels,
            sample_width=self._sample_width_bytes,
        )
        self._push_stream.write(bytes(chunk))

    def drain_partials(self) -> list[AsrResponse]:
        return self._accumulator.drain_partials()

    def stop(self) -> AsrResponse:
        self._accumulator.note_stop_requested()
        self._push_stream.close()
        stop_future = self._recognizer.stop_continuous_recognition_async()
        if hasattr(stop_future, "get"):
            stop_future.get()
        self._stopped.wait(timeout=10.0)
        return self._accumulator.build_final_response()


@register_backend("azure")
class AzureAsrBackend(AsrBackend):
    """Azure Speech SDK integration with normalized output fields."""

    name = "azure"

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
        self.key = env_or(self.config, "speech_key", "AZURE_SPEECH_KEY", "")
        self.region = env_or(self.config, "region", "AZURE_SPEECH_REGION", "")
        self.endpoint = env_or(self.config, "endpoint", "ASR_AZURE_ENDPOINT", "")
        self.streaming_partial_stability_threshold = int(
            env_or(
                self.config,
                "streaming_partial_stability_threshold",
                "ASR_AZURE_STREAM_PARTIAL_STABILITY_THRESHOLD",
                "3",
            )
            or 3
        )
        self._speechsdk: Any = client

    def has_credentials(self) -> bool:
        return bool(self.key and self.region)

    def _load_sdk(self) -> bool:
        if self._speechsdk is not None:
            return True
        try:
            import azure.cognitiveservices.speech as speechsdk

            self._speechsdk = speechsdk
            return True
        except Exception:
            return False

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
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

    def create_stream_session(
        self,
        *,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
    ) -> AzureStreamingSession:
        if not self.key:
            raise RuntimeError("Missing Azure key. Set AZURE_SPEECH_KEY or backends.azure.speech_key.")
        if not self.region:
            raise RuntimeError("Missing Azure region. Set AZURE_SPEECH_REGION or backends.azure.region.")
        if not self._load_sdk():
            raise RuntimeError("Unable to initialize Azure speech SDK")
        return AzureStreamingSession(
            speechsdk=self._speechsdk,
            key=self.key,
            region=self.region,
            endpoint=self.endpoint,
            language=language,
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width_bytes,
            partial_stability_threshold=self.streaming_partial_stability_threshold,
        )

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
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

            speech_config = _build_speech_config(
                self._speechsdk,
                key=self.key,
                region=self.region,
                endpoint=self.endpoint,
                language=language or "en-US",
            )

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
                details = _cancellation_details(self._speechsdk, result)
                return AsrResponse(
                    success=False,
                    error_code="azure_canceled",
                    error_message=str(getattr(details, "error_details", "") or "Azure recognition canceled"),
                    backend_info={"provider": "azure", "model": "speech", "region": self.region},
                    language=language,
                )

            detailed_json = result.properties.get(
                self._speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
                "{}",
            )
            confidence, words = _parse_azure_json(detailed_json, default_confidence=0.0)

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
                raw_response=result,
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
