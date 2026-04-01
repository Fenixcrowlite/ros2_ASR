"""Shared helpers for Hugging Face ASR providers."""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import Any

import numpy as np
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.models import (
    ProviderAudio,
    ProviderMetadata,
    ProviderRuntimeMetrics,
    ProviderStatus,
)


def language_to_hf_token(language: str) -> str:
    text = str(language or "").strip()
    if not text:
        return ""
    return text.split("-", 1)[0].lower()


def resolve_token(credentials_ref: dict[str, str]) -> str:
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACEHUB_API_TOKEN"):
        value = str(credentials_ref.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _pcm_to_float32(data: bytes, *, sample_width_bytes: int, channels: int) -> np.ndarray:
    sample_width = int(sample_width_bytes or 2)
    if sample_width == 1:
        array = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
        array = (array - 128.0) / 128.0
    elif sample_width == 2:
        array = np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 4:
        array = np.frombuffer(data, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported PCM sample width: {sample_width}")

    channel_count = max(int(channels or 1), 1)
    if channel_count > 1 and array.size >= channel_count:
        usable = array[: (array.size // channel_count) * channel_count]
        array = usable.reshape(-1, channel_count).mean(axis=1)
    return np.ascontiguousarray(array, dtype=np.float32)


def _waveform_from_wave_reader(reader: wave.Wave_read) -> tuple[np.ndarray, int, float]:
    channels = int(reader.getnchannels() or 1)
    sample_width = int(reader.getsampwidth() or 2)
    sample_rate = int(reader.getframerate() or 16000)
    frames = reader.readframes(reader.getnframes())
    waveform = _pcm_to_float32(
        frames,
        sample_width_bytes=sample_width,
        channels=channels,
    )
    duration_sec = float(reader.getnframes() / float(sample_rate or 1))
    return waveform, sample_rate, duration_sec


def provider_audio_to_waveform(audio: ProviderAudio) -> tuple[np.ndarray, int, float]:
    """Convert ProviderAudio into mono float32 waveform for transformers pipelines."""
    if audio.wav_path:
        with wave.open(audio.wav_path, "rb") as reader:
            return _waveform_from_wave_reader(reader)
    if audio.audio_bytes:
        raw = bytes(audio.audio_bytes)
        if raw[:4] == b"RIFF":
            with wave.open(io.BytesIO(raw), "rb") as reader:
                return _waveform_from_wave_reader(reader)
        sample_rate = int(audio.sample_rate_hz or 16000)
        channels = int(audio.metadata.get("channels", 1) or 1)
        sample_width = int(audio.metadata.get("sample_width_bytes", 2) or 2)
        waveform = _pcm_to_float32(
            raw,
            sample_width_bytes=sample_width,
            channels=channels,
        )
        duration_sec = float(waveform.size / float(sample_rate or 1))
        return waveform, sample_rate, duration_sec
    raise ValueError("ProviderAudio must contain wav_path or audio_bytes")


def provider_audio_to_wav_bytes(audio: ProviderAudio) -> bytes:
    """Return WAV bytes suitable for HTTP ASR providers."""
    if audio.wav_path:
        return Path(audio.wav_path).read_bytes()
    if audio.audio_bytes:
        raw = bytes(audio.audio_bytes)
        if raw[:4] == b"RIFF":
            return raw
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as writer:
            writer.setnchannels(int(audio.metadata.get("channels", 1) or 1))
            writer.setsampwidth(int(audio.metadata.get("sample_width_bytes", 2) or 2))
            writer.setframerate(int(audio.sample_rate_hz or 16000))
            writer.writeframes(raw)
        return buffer.getvalue()
    raise ValueError("ProviderAudio must contain wav_path or audio_bytes")


def provider_audio_duration_sec(audio: ProviderAudio) -> float:
    if audio.wav_path:
        with wave.open(audio.wav_path, "rb") as reader:
            return float(reader.getnframes() / float(reader.getframerate() or 1))
    if audio.audio_bytes:
        raw = bytes(audio.audio_bytes)
        if raw[:4] == b"RIFF":
            with wave.open(io.BytesIO(raw), "rb") as reader:
                return float(reader.getnframes() / float(reader.getframerate() or 1))
        sample_rate = int(audio.sample_rate_hz or 16000)
        channels = int(audio.metadata.get("channels", 1) or 1)
        sample_width = int(audio.metadata.get("sample_width_bytes", 2) or 2)
        bytes_per_second = max(sample_rate * channels * sample_width, 1)
        return float(len(raw) / float(bytes_per_second))
    return 0.0


def local_timestamp_mode(config: dict[str, Any], *, enable_word_timestamps: bool) -> str | bool | None:
    if not enable_word_timestamps:
        return None
    raw = str(config.get("return_timestamps", "word") or "word").strip().lower()
    if raw in {"", "none", "false", "off", "0"}:
        return None
    if raw in {"segment", "segments", "true", "1", "yes", "on"}:
        return True
    if raw in {"word", "char"}:
        return raw
    return True


def api_return_timestamps(config: dict[str, Any], *, enable_word_timestamps: bool) -> bool:
    if not enable_word_timestamps:
        return False
    raw = str(config.get("return_timestamps", "true") or "true").strip().lower()
    return raw not in {"", "none", "false", "off", "0"}


def transcription_chunks_to_words(chunks: list[dict[str, Any]] | None) -> list[NormalizedWord]:
    words: list[NormalizedWord] = []
    for item in chunks or []:
        text = str(item.get("text", "") or "").strip()
        timestamp = item.get("timestamp", ())
        if not text or not isinstance(timestamp, (list, tuple)) or len(timestamp) != 2:
            continue
        start, end = timestamp
        if start is None or end is None:
            continue
        words.append(
            NormalizedWord(
                word=text,
                start_sec=float(start),
                end_sec=float(end),
                confidence=0.0,
                confidence_available=False,
            )
        )
    return words


def build_transcription_result(
    *,
    provider_id: str,
    audio: ProviderAudio,
    payload: dict[str, Any],
    latency: LatencyMetadata,
    language: str,
    tags: list[str] | None = None,
    raw_metadata_ref: str = "",
) -> NormalizedAsrResult:
    text = str(payload.get("text", "") or "").strip()
    chunks = payload.get("chunks", [])
    chunk_rows = chunks if isinstance(chunks, list) else []
    words = transcription_chunks_to_words(chunk_rows)
    timestamps_available = bool(chunk_rows)
    utterance_start_sec = words[0].start_sec if words else 0.0
    utterance_end_sec = words[-1].end_sec if words else 0.0
    return NormalizedAsrResult(
        request_id=audio.request_id,
        session_id=audio.session_id,
        provider_id=provider_id,
        text=text,
        is_final=True,
        is_partial=False,
        utterance_start_sec=utterance_start_sec,
        utterance_end_sec=utterance_end_sec,
        audio_duration_sec=provider_audio_duration_sec(audio),
        words=words,
        confidence=0.0,
        confidence_available=False,
        timestamps_available=timestamps_available,
        language=language or audio.language,
        language_detected=False,
        latency=latency,
        raw_metadata_ref=raw_metadata_ref,
        degraded=not text,
        error_code="empty_transcript" if not text else "",
        error_message="Provider returned an empty transcript." if not text else "",
        tags=list(tags or []),
    )


class BaseHuggingFaceProvider(AsrProviderAdapter):
    """Non-streaming provider base with shared metadata and runtime metrics."""

    display_name = "Hugging Face"
    implementation = ""
    source = ""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._status = ProviderStatus(provider_id=self.provider_id, state="created")
        self._provider_metadata = ProviderMetadata(
            provider_id=self.provider_id,
            display_name=self.display_name,
            implementation=self.implementation,
            source=self.source,
        )
        self._provider_metrics = ProviderRuntimeMetrics()
        self._latency_total_ms = 0.0

    def _set_metadata(self, **kwargs: Any) -> None:
        metadata = self._provider_metadata
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        metadata.extra.update(
            {
                key: value
                for key, value in kwargs.items()
                if not hasattr(metadata, key)
            }
        )

    def _record_result(self, result: NormalizedAsrResult) -> None:
        metrics = self._provider_metrics
        metrics.requests_total += 1
        metrics.last_latency_ms = float(result.latency.total_ms)
        self._latency_total_ms += float(result.latency.total_ms)
        metrics.average_latency_ms = self._latency_total_ms / float(metrics.requests_total)
        if result.error_code or result.degraded:
            metrics.errors_total += 1
            metrics.last_error_code = result.error_code
            metrics.last_error_message = result.error_message
            self._status = ProviderStatus(
                provider_id=self.provider_id,
                state="degraded",
                health="degraded",
                message="recognize_once completed with degraded result",
                error_code=result.error_code,
                error_message=result.error_message,
            )
        else:
            self._status = ProviderStatus(
                provider_id=self.provider_id,
                state="ready",
                health="ok",
                message="recognize_once completed",
            )

    def _record_exception(self, *, error_code: str, error_message: str) -> None:
        metrics = self._provider_metrics
        metrics.requests_total += 1
        metrics.errors_total += 1
        metrics.last_error_code = error_code
        metrics.last_error_message = error_message
        self._status = ProviderStatus(
            provider_id=self.provider_id,
            state="error",
            health="error",
            message=error_message,
            error_code=error_code,
            error_message=error_message,
        )

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        del options
        raise RuntimeError(f"{type(self).__name__} does not support provider_stream mode")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        del chunk
        raise RuntimeError(f"{type(self).__name__} does not support provider_stream mode")

    def stop_stream(self) -> NormalizedAsrResult:
        raise RuntimeError(f"{type(self).__name__} does not support provider_stream mode")

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")
