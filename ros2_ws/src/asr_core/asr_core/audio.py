from __future__ import annotations

import contextlib
import io
import os
import tempfile
import wave
from collections.abc import Iterable
from pathlib import Path


def read_wav_bytes(wav_path: str) -> bytes:
    with open(wav_path, "rb") as f:
        return f.read()


def wav_duration_sec(wav_path: str) -> float:
    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def wav_info(wav_path: str) -> tuple[int, int, int, int]:
    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()


def bytes_to_temp_wav(audio_bytes: bytes, suffix: str = ".wav") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="asr_audio_")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


def wav_pcm_chunks(wav_path: str, chunk_sec: float) -> list[bytes]:
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
    if path is None:
        return None
    return str(Path(path).expanduser().resolve())


def wav_bytes_to_pcm(audio_bytes: bytes) -> bytes:
    with contextlib.closing(wave.open(io.BytesIO(audio_bytes), "rb")) as wf:
        return wf.readframes(wf.getnframes())


def pcm_chunks_to_wav_bytes(
    chunks: Iterable[bytes], *, sample_rate: int, channels: int = 1, sample_width: int = 2
) -> bytes:
    data = b"".join(chunks)
    buffer = io.BytesIO()
    with contextlib.closing(wave.open(buffer, "wb")) as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(data)
    return buffer.getvalue()
