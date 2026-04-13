"""Local faster-whisper backend with strict device selection."""

from __future__ import annotations

import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

from asr_core.audio import wav_duration_sec
from asr_core.backend import AsrBackend
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp


@register_backend("whisper")
class WhisperAsrBackend(AsrBackend):
    """Whisper integration for high-quality local ASR."""

    name = "whisper"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=False,
            streaming_mode="none",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=False,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        """Parse model/device/decoding parameters from config and ENV."""
        super().__init__(config=config, client=client)
        self.model_size = self.config.get("model_size", os.getenv("ASR_WHISPER_MODEL", "tiny"))
        self.device = self.config.get("device", os.getenv("ASR_WHISPER_DEVICE", "cpu"))
        self.compute_type = self.config.get(
            "compute_type", os.getenv("ASR_WHISPER_COMPUTE_TYPE", "int8")
        )
        self.temperature = float(self.config.get("temperature", 0.0))
        self.no_speech_threshold = float(self.config.get("no_speech_threshold", 0.6))
        cond_prev_raw = self.config.get("condition_on_previous_text", False)
        if isinstance(cond_prev_raw, str):
            self.condition_on_previous_text = cond_prev_raw.lower() in {"1", "true", "yes", "on"}
        else:
            self.condition_on_previous_text = bool(cond_prev_raw)
        vad_filter_raw = self.config.get("vad_filter", True)
        if isinstance(vad_filter_raw, str):
            self.vad_filter = vad_filter_raw.lower() in {"1", "true", "yes", "on"}
        else:
            self.vad_filter = bool(vad_filter_raw)
        self._model: Any = None
        self._load_error: str = ""

    def _load_model(self) -> bool:
        """Lazy-load Whisper model instance."""
        if self._model is not None:
            return True
        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
            self._load_error = ""
            return True
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            if "libcublas.so.12" in detail:
                detail = (
                    f"{detail}. Fix CUDA runtime libraries or set device=cpu explicitly."
                )
            self._load_error = detail
            return False

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
        """Convert request to local WAV path, returning `(path, cleanup_needed)`."""
        if request.wav_path:
            return request.wav_path, False
        if request.audio_bytes:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="whisper_audio_")
            os.close(fd)
            audio_bytes = request.audio_bytes
            if audio_bytes[:4] == b"RIFF":
                with open(tmp_path, "wb") as f:
                    f.write(audio_bytes)
                return tmp_path, True
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(int(request.metadata.get("channels", 1) or 1))
                wf.setsampwidth(int(request.metadata.get("sample_width_bytes", 2) or 2))
                wf.setframerate(int(request.sample_rate or 16000))
                wf.writeframes(audio_bytes)
            return tmp_path, True
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Run one-shot transcription and normalize into unified response."""
        preprocess_start = time.perf_counter()
        language = normalize_language_code(request.language, fallback="en-US")
        if not self._load_model():
            message = "Unable to load faster-whisper model"
            if self._load_error:
                message = f"{message}: {self._load_error}"
            return AsrResponse(
                success=False,
                error_code="whisper_model_error",
                error_message=message,
                backend_info={
                    "provider": "whisper",
                    "model": self.model_size,
                    "region": "local",
                    "compute_device": str(self.device),
                    "compute_type": str(self.compute_type),
                },
                language=language,
            )

        wav_path = ""
        cleanup = False
        try:
            wav_path, cleanup = self._request_to_wav_path(request)
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0
            lang_code = (language or "en").split("-")[0]
            inference_start = time.perf_counter()
            segments, _ = self._model.transcribe(
                wav_path,
                language=lang_code,
                word_timestamps=bool(request.enable_word_timestamps),
                temperature=self.temperature,
                no_speech_threshold=self.no_speech_threshold,
                condition_on_previous_text=self.condition_on_previous_text,
                vad_filter=self.vad_filter,
            )
            segments_list = list(segments)
            inference_ms = (time.perf_counter() - inference_start) * 1000.0
            text = " ".join(seg.text.strip() for seg in segments_list).strip()

            words: list[WordTimestamp] = []
            conf_values: list[float] = []
            for seg in segments_list:
                avg_logprob = getattr(seg, "avg_logprob", None)
                if avg_logprob is not None:
                    conf_values.append(max(0.0, min(1.0, 1.0 + float(avg_logprob) / 5.0)))
                seg_words = getattr(seg, "words", None) or []
                for w in seg_words:
                    prob = float(getattr(w, "probability", 0.0) or 0.0)
                    conf_values.append(prob)
                    words.append(
                        WordTimestamp(
                            word=str(getattr(w, "word", "")).strip(),
                            start_sec=float(getattr(w, "start", 0.0)),
                            end_sec=float(getattr(w, "end", 0.0)),
                            confidence=prob,
                        )
                    )
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0
            post_start = time.perf_counter()
            duration = wav_duration_sec(wav_path)
            post_ms = (time.perf_counter() - post_start) * 1000.0
            return AsrResponse(
                text=text,
                partials=[],
                confidence=avg_conf,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=language,
                backend_info={
                    "provider": "whisper",
                    "model": self.model_size,
                    "region": "local",
                    "compute_device": str(self.device),
                    "compute_type": str(self.compute_type),
                },
                timings=AsrTimings(
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=post_ms,
                ),
                audio_duration_sec=duration,
                success=True,
            )
        except Exception as exc:
            error_message = str(exc)
            if "libcublas.so.12" in error_message:
                error_message = (
                    f"{error_message}. Fix CUDA runtime libraries or set device=cpu explicitly."
                )
            return AsrResponse(
                success=False,
                error_code="whisper_runtime_error",
                error_message=error_message,
                backend_info={
                    "provider": "whisper",
                    "model": self.model_size,
                    "region": "local",
                    "compute_device": str(self.device),
                    "compute_type": str(self.compute_type),
                },
                language=language,
            )
        finally:
            if cleanup and wav_path and Path(wav_path).exists():
                Path(wav_path).unlink(missing_ok=True)

    def streaming_recognize(self, chunks, *, language: str, sample_rate: int) -> AsrResponse:
        """Reject streaming calls explicitly; Whisper is batch-only here."""
        del chunks, language, sample_rate
        raise NotImplementedError("WhisperAsrBackend does not support streaming_recognize")
