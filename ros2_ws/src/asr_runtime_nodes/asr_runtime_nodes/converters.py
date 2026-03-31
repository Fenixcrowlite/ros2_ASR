"""Converters between core normalized models and ROS2 interface messages."""

from __future__ import annotations

from collections.abc import Iterable

from asr_core.normalized import NormalizedAsrResult
from asr_interfaces.msg import AsrResult, AsrResultPartial, WordTimestamp
from builtin_interfaces.msg import Time


def _sec_to_time(value: float) -> Time:
    msg = Time()
    if value <= 0:
        return msg
    whole = int(value)
    msg.sec = whole
    msg.nanosec = int((value - whole) * 1_000_000_000)
    return msg


def to_asr_result_msg(result: NormalizedAsrResult) -> AsrResult:
    msg = AsrResult()
    msg.request_id = result.request_id
    msg.session_id = result.session_id
    msg.provider_id = result.provider_id
    msg.backend = result.provider_id
    msg.text = result.text
    msg.partials = []
    msg.audio_duration_sec = float(result.audio_duration_sec)
    msg.confidence = float(result.confidence)
    msg.confidence_available = bool(result.confidence_available)
    msg.word_timestamps = [
        WordTimestamp(
            word=item.word,
            start_sec=float(item.start_sec),
            end_sec=float(item.end_sec),
            confidence=float(item.confidence),
            confidence_available=bool(item.confidence_available),
        )
        for item in result.words
    ]
    msg.timestamps_available = bool(result.timestamps_available)
    msg.language = result.language
    msg.is_final = bool(result.is_final)
    msg.is_partial = bool(result.is_partial)
    msg.success = not result.degraded and not result.error_code
    msg.error_code = result.error_code
    msg.error_message = result.error_message
    msg.utterance_start = _sec_to_time(result.utterance_start_sec)
    msg.utterance_end = _sec_to_time(result.utterance_end_sec)
    msg.preprocess_ms = float(result.latency.preprocess_ms)
    msg.inference_ms = float(result.latency.inference_ms)
    msg.postprocess_ms = float(result.latency.postprocess_ms)
    msg.total_ms = float(result.latency.total_ms)
    msg.first_partial_latency_ms = float(result.latency.first_partial_ms)
    msg.finalization_latency_ms = float(result.latency.finalization_ms)
    msg.raw_metadata_ref = result.raw_metadata_ref
    msg.degraded = bool(result.degraded)
    msg.tags = list(result.tags)
    return msg


def to_partial_msg(result: NormalizedAsrResult) -> AsrResultPartial:
    msg = AsrResultPartial()
    msg.session_id = result.session_id
    msg.request_id = result.request_id
    msg.provider_id = result.provider_id
    msg.text = result.text
    msg.confidence = float(result.confidence)
    msg.confidence_available = bool(result.confidence_available)
    msg.partial_latency_ms = float(result.latency.first_partial_ms)
    msg.language = result.language
    msg.raw_metadata_ref = result.raw_metadata_ref
    return msg


def build_partial_from_text(
    *,
    session_id: str,
    request_id: str,
    provider_id: str,
    text_tokens: Iterable[str],
    language: str,
) -> AsrResultPartial:
    text = " ".join(text_tokens).strip()
    result = NormalizedAsrResult(
        request_id=request_id,
        session_id=session_id,
        provider_id=provider_id,
        text=text,
        is_final=False,
        is_partial=True,
        language=language,
    )
    return to_partial_msg(result)
