"""Local Vosk backend (offline ASR, native streaming support)."""

from __future__ import annotations

import json
import os
import tempfile
import time
import wave
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path
from typing import Any

from asr_core.audio import wav_duration_sec
from asr_core.backend import AsrBackend
from asr_core.factory import register_backend
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp


@register_backend("vosk")
class VoskAsrBackend(AsrBackend):
    """Vosk integration with one-shot and native chunk streaming modes."""

    name = "vosk"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=True,
            streaming_mode="native",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=False,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        """Read model path from config/ENV and lazy-load Vosk model."""
        super().__init__(config=config, client=client)
        self.model_path = self.config.get("model_path") or os.getenv("VOSK_MODEL_PATH", "")
        self._model: Any = None
        self._vosk_module: Any = None

    def _load_vosk(self) -> bool:
        """Load Vosk module/model once."""
        if self._model is not None:
            return True
        if not self.model_path:
            return False
        try:
            from vosk import Model

            self._vosk_module = __import__("vosk")
            self._model = Model(self.model_path)
            return True
        except Exception:
            return False

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
        """Convert request to local WAV path, returning `(path, cleanup_needed)`."""
        if request.wav_path:
            return request.wav_path, False
        if request.audio_bytes:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="vosk_audio_")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(request.audio_bytes)
            return tmp_path, True
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        """Run full-file recognition with Vosk KaldiRecognizer."""
        preprocess_start = time.perf_counter()
        if not self._load_vosk():
            return AsrResponse(
                success=False,
                error_code="vosk_model_missing",
                error_message="Vosk model is not configured or failed to load",
                backend_info={"provider": "vosk", "model": str(self.model_path), "region": "local"},
                language=request.language,
            )

        wav_path = ""
        cleanup = False
        partials: list[str] = []
        try:
            wav_path, cleanup = self._request_to_wav_path(request)
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0

            inference_start = time.perf_counter()
            with closing(wave.open(wav_path, "rb")) as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    return AsrResponse(
                        success=False,
                        error_code="invalid_audio",
                        error_message="Vosk requires mono 16-bit PCM WAV",
                        backend_info={
                            "provider": "vosk",
                            "model": str(self.model_path),
                            "region": "local",
                        },
                        language=request.language,
                    )
                sample_rate = wf.getframerate()
                rec = self._vosk_module.KaldiRecognizer(self._model, sample_rate)
                rec.SetWords(bool(request.enable_word_timestamps))
                while True:
                    data = wf.readframes(4000)
                    if not data:
                        break
                    accepted = rec.AcceptWaveform(data)
                    if not accepted:
                        partial = json.loads(rec.PartialResult()).get("partial", "")
                        if partial:
                            partials.append(partial)
                final = json.loads(rec.FinalResult())
            inference_ms = (time.perf_counter() - inference_start) * 1000.0

            text = final.get("text", "")
            word_items = final.get("result", [])
            words: list[WordTimestamp] = []
            confidences: list[float] = []
            for item in word_items:
                conf = float(item.get("conf", 0.0))
                confidences.append(conf)
                words.append(
                    WordTimestamp(
                        word=item.get("word", ""),
                        start_sec=float(item.get("start", 0.0)),
                        end_sec=float(item.get("end", 0.0)),
                        confidence=conf,
                    )
                )
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            post_start = time.perf_counter()
            duration = wav_duration_sec(wav_path)
            post_ms = (time.perf_counter() - post_start) * 1000.0
            return AsrResponse(
                text=text,
                partials=partials,
                confidence=avg_conf,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=request.language,
                backend_info={"provider": "vosk", "model": str(self.model_path), "region": "local"},
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
                error_code="vosk_runtime_error",
                error_message=str(exc),
                backend_info={"provider": "vosk", "model": str(self.model_path), "region": "local"},
                language=request.language,
            )
        finally:
            if cleanup and wav_path and Path(wav_path).exists():
                Path(wav_path).unlink(missing_ok=True)

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        """Run native chunk-by-chunk recognition and aggregate partials."""
        if not self._load_vosk():
            return AsrResponse(
                success=False,
                error_code="vosk_model_missing",
                error_message="Vosk model is not configured or failed to load",
                backend_info={"provider": "vosk", "model": str(self.model_path), "region": "local"},
                language=language,
            )
        start = time.perf_counter()
        rec = self._vosk_module.KaldiRecognizer(self._model, sample_rate)
        rec.SetWords(True)
        partials: list[str] = []
        total_bytes = 0
        for chunk in chunks:
            total_bytes += len(chunk)
            accepted = rec.AcceptWaveform(chunk)
            if not accepted:
                partial = json.loads(rec.PartialResult()).get("partial", "")
                if partial:
                    partials.append(partial)
        final = json.loads(rec.FinalResult())
        words = [
            WordTimestamp(
                word=item.get("word", ""),
                start_sec=float(item.get("start", 0.0)),
                end_sec=float(item.get("end", 0.0)),
                confidence=float(item.get("conf", 0.0)),
            )
            for item in final.get("result", [])
        ]
        confidences = [w.confidence for w in words if w.confidence > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        duration = total_bytes / float(max(sample_rate * 2, 1))
        return AsrResponse(
            text=final.get("text", ""),
            partials=partials,
            confidence=avg_conf,
            word_timestamps=words,
            language=language,
            backend_info={"provider": "vosk", "model": str(self.model_path), "region": "local"},
            timings=AsrTimings(preprocess_ms=0.0, inference_ms=elapsed_ms, postprocess_ms=1.0),
            audio_duration_sec=duration,
            success=True,
        )
