"""Helpers for native streaming backends/providers.

This module centralizes the mechanics that every native streaming session
needs: partial deduplication, latency bookkeeping, final aggregation and
thread-safe delivery of stream updates to provider adapters.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .models import AsrResponse, AsrTimings, WordTimestamp


@dataclass(slots=True)
class StreamAccumulator:
    """Collect partial/final events for one native streaming session."""

    provider: str
    language: str
    model: str = ""
    region: str = ""
    audio_duration_sec: float = 0.0
    _started_at: float = field(default_factory=time.perf_counter, init=False, repr=False)
    _stop_requested_at: float = field(default=0.0, init=False, repr=False)
    _first_partial_ms: float = field(default=0.0, init=False, repr=False)
    _last_partial_text: str = field(default="", init=False, repr=False)
    _partial_count: int = field(default=0, init=False, repr=False)
    _final_segments: list[str] = field(default_factory=list, init=False, repr=False)
    _words: list[WordTimestamp] = field(default_factory=list, init=False, repr=False)
    _confidences: list[float] = field(default_factory=list, init=False, repr=False)
    _error_code: str = field(default="", init=False, repr=False)
    _error_message: str = field(default="", init=False, repr=False)
    _raw_response: Any = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _partials: queue.SimpleQueue[AsrResponse] = field(
        default_factory=queue.SimpleQueue,
        init=False,
        repr=False,
    )

    def _base_backend_info(self) -> dict[str, str]:
        info = {"provider": self.provider, "streaming_mode": "native"}
        if self.model:
            info["model"] = self.model
        if self.region:
            info["region"] = self.region
        return info

    def mark_partial(
        self,
        text: str,
        *,
        confidence: float = 0.0,
        language: str = "",
        backend_info: dict[str, Any] | None = None,
        raw_response: Any = None,
    ) -> None:
        partial_text = str(text or "").strip()
        if not partial_text:
            return

        with self._lock:
            if partial_text == self._last_partial_text:
                return
            elapsed_ms = (time.perf_counter() - self._started_at) * 1000.0
            if self._first_partial_ms <= 0.0:
                self._first_partial_ms = float(elapsed_ms)
            self._last_partial_text = partial_text
            self._partial_count += 1
            merged_info = self._base_backend_info()
            for key, value in (backend_info or {}).items():
                if value is None:
                    continue
                merged_info[str(key)] = str(value)
            merged_info["first_partial_ms"] = f"{self._first_partial_ms:.3f}"
            merged_info["partial_count"] = str(self._partial_count)
            self._partials.put(
                AsrResponse(
                    text=partial_text,
                    partials=[partial_text],
                    confidence=float(confidence or 0.0),
                    language=str(language or self.language),
                    backend_info=merged_info,
                    timings=AsrTimings(postprocess_ms=float(elapsed_ms)),
                    audio_duration_sec=float(self.audio_duration_sec or 0.0),
                    success=True,
                    raw_response=raw_response,
                )
            )

    def add_final(
        self,
        text: str,
        *,
        words: list[WordTimestamp] | None = None,
        confidence: float = 0.0,
        language: str = "",
        backend_info: dict[str, Any] | None = None,
        raw_response: Any = None,
    ) -> None:
        final_text = str(text or "").strip()
        merged_words = words or []
        with self._lock:
            if final_text:
                self._final_segments.append(final_text)
                self._last_partial_text = ""
            if merged_words:
                self._words.extend(merged_words)
            if float(confidence or 0.0) > 0.0:
                self._confidences.append(float(confidence))
            if language:
                self.language = str(language)
            if raw_response is not None:
                self._raw_response = raw_response
            if backend_info:
                for key, value in backend_info.items():
                    if key == "model" and value:
                        self.model = str(value)
                    if key == "region" and value:
                        self.region = str(value)

    def set_error(self, error_code: str, error_message: str, *, raw_response: Any = None) -> None:
        with self._lock:
            self._error_code = str(error_code or "stream_runtime_error")
            self._error_message = str(error_message or self._error_code)
            if raw_response is not None:
                self._raw_response = raw_response

    def note_stop_requested(self) -> None:
        with self._lock:
            if self._stop_requested_at <= 0.0:
                self._stop_requested_at = time.perf_counter()

    def drain_partials(self) -> list[AsrResponse]:
        items: list[AsrResponse] = []
        while True:
            try:
                items.append(self._partials.get_nowait())
            except queue.Empty:
                break
        return items

    def build_final_response(self) -> AsrResponse:
        with self._lock:
            total_ms = (time.perf_counter() - self._started_at) * 1000.0
            if self._stop_requested_at > 0.0:
                finalization_ms = max((time.perf_counter() - self._stop_requested_at) * 1000.0, 0.0)
            else:
                finalization_ms = 0.0

            text = " ".join(segment for segment in self._final_segments if segment).strip()
            avg_conf = sum(self._confidences) / len(self._confidences) if self._confidences else 0.0
            success = not self._error_code
            error_code = self._error_code
            error_message = self._error_message
            if success and not text:
                success = False
                error_code = "empty_transcript"
                error_message = "Native streaming completed without a final transcript."

            backend_info = self._base_backend_info()
            if self._first_partial_ms > 0.0:
                backend_info["first_partial_ms"] = f"{self._first_partial_ms:.3f}"
            backend_info["finalization_ms"] = f"{finalization_ms:.3f}"
            backend_info["partial_count"] = str(self._partial_count)

            inference_ms = max(total_ms - finalization_ms, 0.0)
            return AsrResponse(
                text=text,
                partials=[],
                confidence=float(avg_conf),
                word_timestamps=list(self._words),
                language=self.language,
                backend_info=backend_info,
                timings=AsrTimings(
                    preprocess_ms=0.0,
                    inference_ms=float(inference_ms),
                    postprocess_ms=float(finalization_ms),
                ),
                audio_duration_sec=float(self.audio_duration_sec or 0.0),
                success=success,
                error_code=error_code,
                error_message=error_message,
                raw_response=self._raw_response,
            )
