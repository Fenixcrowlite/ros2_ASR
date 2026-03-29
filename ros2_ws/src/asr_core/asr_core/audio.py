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
from math import sqrt
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


def looks_like_wav_bytes(audio_bytes: bytes) -> bool:
    """Return `True` when payload starts with a RIFF/WAVE header."""
    return len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"


def wav_duration_bytes(audio_bytes: bytes) -> float:
    """Return WAV duration in seconds for an in-memory RIFF/WAVE payload."""
    with contextlib.closing(wave.open(io.BytesIO(audio_bytes), "rb")) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def wav_info_bytes(audio_bytes: bytes) -> tuple[int, int, int, int]:
    """Return `(sample_rate, channels, sample_width_bytes, n_frames)` for WAV bytes."""
    with contextlib.closing(wave.open(io.BytesIO(audio_bytes), "rb")) as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()


def sample_width_from_encoding(encoding: str | None, default: int = 2) -> int:
    """Infer sample width in bytes from an encoding label such as `pcm_s16le`."""
    text = str(encoding or "").lower()
    if "24" in text:
        return 3
    if "32" in text or "float" in text:
        return 4
    if "8" in text or text.endswith("u8"):
        return 1
    if "16" in text:
        return 2
    return default


def pcm_signed_from_encoding(encoding: str | None, default: bool = True) -> bool:
    """Infer signed-vs-unsigned PCM from an encoding label."""
    text = str(encoding or "").lower()
    if not text:
        return default
    if "u8" in text or "unsigned" in text:
        return False
    return True


def _pcm_clip_bounds(sample_width: int, *, signed: bool) -> tuple[int, int]:
    if sample_width <= 0 or sample_width > 4:
        raise ValueError(f"Unsupported PCM sample width: {sample_width}")
    if sample_width == 1 and not signed:
        return -128, 127
    bits = sample_width * 8
    if signed:
        limit = 1 << (bits - 1)
        return -limit, limit - 1
    return 0, (1 << bits) - 1


def pcm_peak_limit(sample_width: int, *, signed: bool = True) -> int:
    """Return maximum intended absolute magnitude for normalized PCM samples."""
    low, high = _pcm_clip_bounds(sample_width, signed=signed)
    return max(abs(low), abs(high))


def pcm_decode_samples(audio_bytes: bytes, *, sample_width: int, signed: bool = True) -> list[int]:
    """Decode little-endian PCM bytes into integer samples."""
    if sample_width <= 0:
        raise ValueError("sample_width must be > 0")
    usable = len(audio_bytes) - (len(audio_bytes) % sample_width)
    if usable <= 0:
        return []
    payload = audio_bytes[:usable]
    if sample_width == 1 and not signed:
        return [value - 128 for value in payload]
    return [
        int.from_bytes(payload[offset : offset + sample_width], byteorder="little", signed=signed)
        for offset in range(0, usable, sample_width)
    ]


def pcm_encode_samples(
    samples: Iterable[float | int], *, sample_width: int, signed: bool = True
) -> bytes:
    """Encode integer samples into little-endian PCM bytes with saturation."""
    lo, hi = _pcm_clip_bounds(sample_width, signed=signed)
    encoded = bytearray()
    for sample in samples:
        clipped = max(lo, min(hi, int(round(sample))))
        if sample_width == 1 and not signed:
            encoded.append(clipped + 128)
        else:
            encoded.extend(int(clipped).to_bytes(sample_width, byteorder="little", signed=signed))
    return bytes(encoded)


def pcm_rms(audio_bytes: bytes, *, sample_width: int, signed: bool = True) -> float:
    """Compute RMS energy for PCM payload."""
    samples = pcm_decode_samples(audio_bytes, sample_width=sample_width, signed=signed)
    if not samples:
        return 0.0
    mean_square = sum(sample * sample for sample in samples) / float(len(samples))
    return sqrt(mean_square)


def pcm_max_abs(audio_bytes: bytes, *, sample_width: int, signed: bool = True) -> int:
    """Return peak absolute sample magnitude."""
    samples = pcm_decode_samples(audio_bytes, sample_width=sample_width, signed=signed)
    if not samples:
        return 0
    return max(abs(sample) for sample in samples)


def pcm_scale(
    audio_bytes: bytes, *, sample_width: int, factor: float, signed: bool = True
) -> bytes:
    """Scale PCM payload with saturation."""
    if not audio_bytes:
        return b""
    samples = pcm_decode_samples(audio_bytes, sample_width=sample_width, signed=signed)
    scaled = [sample * factor for sample in samples]
    return pcm_encode_samples(scaled, sample_width=sample_width, signed=signed)


def pcm_mix(
    primary: bytes,
    secondary: bytes,
    *,
    sample_width: int,
    signed: bool = True,
) -> bytes:
    """Sample-wise add two PCM payloads with saturation."""
    left = pcm_decode_samples(primary, sample_width=sample_width, signed=signed)
    right = pcm_decode_samples(secondary, sample_width=sample_width, signed=signed)
    usable = min(len(left), len(right))
    if usable <= 0:
        return b""
    mixed = [left[index] + right[index] for index in range(usable)]
    return pcm_encode_samples(mixed, sample_width=sample_width, signed=signed)


def pcm_to_mono(
    audio_bytes: bytes,
    *,
    sample_width: int,
    channels: int,
    signed: bool = True,
    left_gain: float = 0.5,
    right_gain: float = 0.5,
) -> bytes:
    """Collapse interleaved PCM stereo into mono."""
    if channels <= 1 or not audio_bytes:
        return audio_bytes
    samples = pcm_decode_samples(audio_bytes, sample_width=sample_width, signed=signed)
    usable = len(samples) - (len(samples) % channels)
    if usable <= 0:
        return b""
    samples = samples[:usable]
    mono: list[float] = []
    if channels == 2:
        for offset in range(0, usable, 2):
            mono.append((samples[offset] * left_gain) + (samples[offset + 1] * right_gain))
    else:
        for offset in range(0, usable, channels):
            frame = samples[offset : offset + channels]
            mono.append(sum(frame) / float(channels))
    return pcm_encode_samples(mono, sample_width=sample_width, signed=signed)


def pcm_resample_linear(
    audio_bytes: bytes,
    *,
    sample_width: int,
    channels: int,
    source_rate_hz: int,
    target_rate_hz: int,
    signed: bool = True,
) -> bytes:
    """Resample PCM payload using deterministic linear interpolation."""
    if not audio_bytes or source_rate_hz == target_rate_hz:
        return audio_bytes
    if channels <= 0:
        raise ValueError("channels must be > 0")
    if source_rate_hz <= 0 or target_rate_hz <= 0:
        raise ValueError("source_rate_hz and target_rate_hz must be > 0")

    samples = pcm_decode_samples(audio_bytes, sample_width=sample_width, signed=signed)
    usable = len(samples) - (len(samples) % channels)
    if usable <= 0:
        return b""
    samples = samples[:usable]
    frame_count = usable // channels
    if frame_count <= 1:
        return pcm_encode_samples(samples, sample_width=sample_width, signed=signed)

    target_frames = max(
        int(round(frame_count * (float(target_rate_hz) / float(source_rate_hz)))), 1
    )
    resampled: list[float] = []
    for target_index in range(target_frames):
        source_position = target_index * (float(source_rate_hz) / float(target_rate_hz))
        left_index = int(source_position)
        right_index = min(left_index + 1, frame_count - 1)
        ratio = source_position - float(left_index)
        for channel_index in range(channels):
            left_sample = samples[(left_index * channels) + channel_index]
            right_sample = samples[(right_index * channels) + channel_index]
            interpolated = left_sample + ((right_sample - left_sample) * ratio)
            resampled.append(interpolated)
    return pcm_encode_samples(resampled, sample_width=sample_width, signed=signed)


def pcm_duration_sec(
    audio_bytes: bytes,
    *,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,
) -> float:
    """Estimate PCM duration in seconds from payload size and stream metadata."""
    bytes_per_frame = max(int(channels or 1) * int(sample_width or 2), 1)
    frames = len(audio_bytes) / float(bytes_per_frame)
    return frames / float(max(int(sample_rate or 16000), 1))


def audio_bytes_to_temp_wav(
    audio_bytes: bytes,
    *,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,
    prefix: str = "asr_audio_",
) -> str:
    """Persist either WAV bytes or raw PCM bytes as a valid temporary WAV file."""
    fd, path = tempfile.mkstemp(suffix=".wav", prefix=prefix)
    os.close(fd)
    if looks_like_wav_bytes(audio_bytes):
        with open(path, "wb") as f:
            f.write(audio_bytes)
        return path
    with contextlib.closing(wave.open(path, "wb")) as wf:
        wf.setnchannels(int(channels or 1))
        wf.setsampwidth(int(sample_width or 2))
        wf.setframerate(int(sample_rate or 16000))
        wf.writeframes(audio_bytes)
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

    This utility is shared by tools/tests that need a deterministic WAV wrapper
    for raw PCM chunks.
    """
    data = b"".join(chunks)
    buffer = io.BytesIO()
    with contextlib.closing(wave.open(buffer, "wb")) as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)
    return buffer.getvalue()
