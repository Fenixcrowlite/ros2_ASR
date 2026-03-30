"""Vosk local provider adapter."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from asr_backend_vosk.backend import VoskAsrBackend
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
        audio_duration_sec=float(getattr(response, "audio_duration_sec", 0.0) or 0.0),
        words=words,
        confidence=float(response.confidence),
        confidence_available=response.confidence > 0,
        timestamps_available=bool(words),
        language=response.language,
        latency=LatencyMetadata(
            total_ms=float(response.timings.total_ms),
            preprocess_ms=float(response.timings.preprocess_ms),
            inference_ms=float(response.timings.inference_ms),
            postprocess_ms=float(response.timings.postprocess_ms),
        ),
        degraded=not response.success,
        error_code=response.error_code,
        error_message=response.error_message,
    )


class VoskProvider(AsrProviderAdapter):
    provider_id = "vosk"

    def __init__(self) -> None:
        self._backend: VoskAsrBackend | None = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._stream_chunks: list[bytes] = []
        self._stream_language = "en-US"
        self._stream_rate = 16000
        self._stream_session_id = "stream"
        self._stream_request_id = "stream"
        self._stream_started_at = 0.0
        self._stream_first_partial_ms = 0.0
        self._stream_recognizer: Any = None

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        del credentials_ref
        self._backend = VoskAsrBackend(config=config)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._backend is None:
            return ["Provider is not initialized"]
        if not self._backend.model_path:
            return ["model_path is required for Vosk"]
        model_dir = Path(str(self._backend.model_path))
        if not model_dir.exists():
            return [f"model_path does not exist: {model_dir}"]
        if not model_dir.is_dir():
            return [f"model_path is not a directory: {model_dir}"]
        visible_entries = [item for item in model_dir.iterdir() if item.name != ".gitkeep"]
        if not visible_entries:
            return [f"model_path does not contain a Vosk model: {model_dir}"]
        return []

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
            raise RuntimeError("VoskProvider is not initialized")
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
        opts = options or {}
        if self._backend is None:
            raise RuntimeError("VoskProvider is not initialized")
        if not self._backend._load_vosk():  # noqa: SLF001 - provider owns backend session lifecycle
            detail = str(getattr(self._backend, "_last_load_error", "") or "").strip()
            message = "Vosk model is not configured or failed to load"
            if detail:
                message = f"{message}: {detail}"
            raise RuntimeError(message)
        self._stream_chunks = []
        self._stream_language = str(opts.get("language", "en-US"))
        self._stream_rate = int(opts.get("sample_rate_hz", 16000))
        self._stream_session_id = str(opts.get("session_id", "stream") or "stream")
        self._stream_request_id = str(opts.get("request_id", "stream") or "stream")
        self._stream_started_at = time.perf_counter()
        self._stream_first_partial_ms = 0.0
        self._stream_recognizer = self._backend._vosk_module.KaldiRecognizer(self._backend._model, self._stream_rate)  # noqa: SLF001
        self._stream_recognizer.SetWords(True)
        self._status = ProviderStatus(provider_id=self.provider_id, state="streaming")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        if self._stream_recognizer is None:
            raise RuntimeError("Vosk stream is not active")
        self._stream_chunks.append(chunk)
        accepted = self._stream_recognizer.AcceptWaveform(chunk)
        if accepted:
            return None
        partial = json.loads(self._stream_recognizer.PartialResult()).get("partial", "").strip()
        if not partial:
            return None
        elapsed_ms = (time.perf_counter() - self._stream_started_at) * 1000.0 if self._stream_started_at else 0.0
        if self._stream_first_partial_ms <= 0.0:
            self._stream_first_partial_ms = float(elapsed_ms)
        return NormalizedAsrResult(
            request_id=self._stream_request_id,
            session_id=self._stream_session_id,
            provider_id=self.provider_id,
            text=partial,
            is_final=False,
            is_partial=True,
            language=self._stream_language,
            latency=LatencyMetadata(
                total_ms=float(elapsed_ms),
                preprocess_ms=0.0,
                inference_ms=float(elapsed_ms),
                postprocess_ms=0.0,
                first_partial_ms=float(self._stream_first_partial_ms or elapsed_ms),
            ),
            confidence=0.0,
            confidence_available=False,
            timestamps_available=False,
        )

    def stop_stream(self) -> NormalizedAsrResult:
        if self._backend is None:
            raise RuntimeError("VoskProvider is not initialized")
        if self._stream_recognizer is None:
            raise RuntimeError("Vosk stream is not active")

        final = json.loads(self._stream_recognizer.FinalResult())
        words = [
            NormalizedWord(
                word=str(item.get("word", "")),
                start_sec=float(item.get("start", 0.0)),
                end_sec=float(item.get("end", 0.0)),
                confidence=float(item.get("conf", 0.0)),
                confidence_available=float(item.get("conf", 0.0)) > 0.0,
            )
            for item in final.get("result", [])
        ]
        confidences = [word.confidence for word in words if word.confidence > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        elapsed_ms = (time.perf_counter() - self._stream_started_at) * 1000.0 if self._stream_started_at else 0.0
        duration_sec = sum(len(chunk) for chunk in self._stream_chunks) / float(max(self._stream_rate * 2, 1))
        result = NormalizedAsrResult(
            request_id=self._stream_request_id,
            session_id=self._stream_session_id,
            provider_id=self.provider_id,
            text=str(final.get("text", "")).strip(),
            is_final=True,
            is_partial=False,
            utterance_start_sec=words[0].start_sec if words else 0.0,
            utterance_end_sec=words[-1].end_sec if words else duration_sec,
            words=words,
            confidence=float(avg_conf),
            confidence_available=bool(confidences),
            timestamps_available=bool(words),
            language=self._stream_language,
            latency=LatencyMetadata(
                total_ms=float(elapsed_ms),
                preprocess_ms=0.0,
                inference_ms=max(float(elapsed_ms) - 1.0, 0.0),
                postprocess_ms=1.0,
                first_partial_ms=float(self._stream_first_partial_ms),
                finalization_ms=1.0,
            ),
        )
        self._stream_recognizer = None
        self._stream_chunks = []
        self._status = ProviderStatus(provider_id=self.provider_id, state="ready")
        return result

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._stream_recognizer = None
        self._stream_chunks = []
        self._stream_started_at = 0.0
        self._stream_first_partial_ms = 0.0
        self._backend = None
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
