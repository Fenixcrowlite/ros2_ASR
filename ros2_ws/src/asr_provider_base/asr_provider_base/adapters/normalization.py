"""Shared response normalization helpers for provider adapters."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord

from asr_provider_base.models import ProviderAudio


def backend_info_float(response: Any, key: str) -> float:
    """Extract float metadata from backend_info without leaking provider specifics."""
    backend_info = getattr(response, "backend_info", {}) or {}
    value = backend_info.get(key, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_words(items: Iterable[Any]) -> list[NormalizedWord]:
    """Convert provider/backend word timestamps into normalized runtime words."""
    words: list[NormalizedWord] = []
    for item in items or []:
        confidence = float(getattr(item, "confidence", 0.0) or 0.0)
        words.append(
            NormalizedWord(
                word=str(getattr(item, "word", "") or "").strip(),
                start_sec=float(getattr(item, "start_sec", 0.0) or 0.0),
                end_sec=float(getattr(item, "end_sec", 0.0) or 0.0),
                confidence=confidence,
                confidence_available=confidence > 0.0,
            )
        )
    return words


def normalize_backend_response(
    *,
    provider_id: str,
    audio: ProviderAudio,
    response: Any,
    is_partial: bool = False,
    tags: Iterable[str] = (),
    language_detected: bool = False,
    raw_metadata_ref: str = "",
    allow_empty_final: bool = False,
    empty_transcript_error_code: str = "empty_transcript",
    empty_transcript_error_message: str = "",
) -> NormalizedAsrResult:
    """Build a NormalizedAsrResult from a backend/provider response object."""
    words = normalize_words(getattr(response, "word_timestamps", []) or [])
    text = str(getattr(response, "text", "") or "").strip()
    success = bool(getattr(response, "success", True))
    error_code = str(getattr(response, "error_code", "") or "")
    error_message = str(getattr(response, "error_message", "") or "")
    degraded = not success
    if not is_partial and not degraded and not allow_empty_final and not text:
        degraded = True
        error_code = error_code or empty_transcript_error_code
        error_message = error_message or (
            empty_transcript_error_message or "Provider returned an empty transcript."
        )

    confidence = float(getattr(response, "confidence", 0.0) or 0.0)
    timings = getattr(response, "timings", None)
    preprocess_ms = float(getattr(timings, "preprocess_ms", 0.0) or 0.0)
    inference_ms = float(getattr(timings, "inference_ms", 0.0) or 0.0)
    postprocess_ms = float(getattr(timings, "postprocess_ms", 0.0) or 0.0)
    total_ms = float(getattr(timings, "total_ms", 0.0) or 0.0)
    if total_ms <= 0.0:
        total_ms = preprocess_ms + inference_ms + postprocess_ms

    return NormalizedAsrResult(
        request_id=audio.request_id,
        session_id=audio.session_id,
        provider_id=provider_id,
        text=text,
        is_final=not is_partial,
        is_partial=is_partial,
        utterance_start_sec=words[0].start_sec if words else 0.0,
        utterance_end_sec=words[-1].end_sec if words else 0.0,
        audio_duration_sec=float(getattr(response, "audio_duration_sec", 0.0) or 0.0),
        words=words,
        confidence=confidence,
        confidence_available=confidence > 0.0,
        timestamps_available=bool(words),
        language=str(getattr(response, "language", "") or audio.language or ""),
        language_detected=bool(language_detected),
        latency=LatencyMetadata(
            total_ms=total_ms,
            preprocess_ms=preprocess_ms,
            inference_ms=inference_ms,
            postprocess_ms=postprocess_ms,
            first_partial_ms=backend_info_float(response, "first_partial_ms"),
            finalization_ms=backend_info_float(response, "finalization_ms"),
        ),
        raw_metadata_ref=raw_metadata_ref,
        degraded=degraded,
        error_code=error_code,
        error_message=error_message,
        tags=[str(item) for item in tags],
    )
