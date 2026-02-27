"""Audio utility helpers shared by all ASR backends.

This module centralizes the low-level WAV/PCM conversions so every backend
handles audio in a consistent way.
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import wave
from collections.abc import Iterable
from pathlib import Path


def read_wav_bytes(wav_path: str) -> bytes:
    """Return raw bytes of a WAV file from disk."""
    with open(wav_path, "rb") as f:
        return f.read()


def wav_duration_sec(wav_path: str) -> float:
    """Return WAV duration in seconds."""
    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def wav_info(wav_path: str) -> tuple[int, int, int, int]:
    """Return `(sample_rate, channels, sample_width_bytes, n_frames)`."""
    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()


def bytes_to_temp_wav(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """Persist bytes into a temporary WAV-like file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="asr_audio_")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


def wav_pcm_chunks(wav_path: str, chunk_sec: float) -> list[bytes]:
    """Split WAV payload into PCM chunks for streaming simulation.

    Args:
        wav_path: Path to mono/stereo PCM WAV file.
        chunk_sec: Chunk duration in seconds.
    """
    if chunk_sec <= 0:
        raise ValueError("chunk_sec must be > 0")
    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        frame_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frames_per_chunk = int(frame_rate * chunk_sec)
        bytes_per_frame = channels * sample_width
        chunks: list[bytes] = []
        while True:
            frame_data = wf.readframes(frames_per_chunk)
            if not frame_data:
                break
            if len(frame_data) % bytes_per_frame != 0:
                break
            chunks.append(frame_data)
        return chunks


def maybe_resolve_path(path: str | None) -> str | None:
    """Resolve `~` and relative paths. Return `None` unchanged."""
    if path is None:
        return None
    return str(Path(path).expanduser().resolve())


def wav_bytes_to_pcm(audio_bytes: bytes) -> bytes:
    """Extract pure PCM frames from WAV bytes."""
    with contextlib.closing(wave.open(io.BytesIO(audio_bytes), "rb")) as wf:
        return wf.readframes(wf.getnframes())


def pcm_chunks_to_wav_bytes(
    chunks: Iterable[bytes], *, sample_rate: int, channels: int = 1, sample_width: int = 2
) -> bytes:
    """Wrap raw PCM chunks into a valid in-memory WAV stream.

    This is used by generic streaming fallback:
    `chunks` -> temporary WAV bytes -> backend `recognize_once`.
    """
    data = b"".join(chunks)
    buffer = io.BytesIO()
    with contextlib.closing(wave.open(buffer, "wb")) as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)
    return buffer.getvalue()
