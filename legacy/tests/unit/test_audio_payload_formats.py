from __future__ import annotations

import wave
from pathlib import Path

from asr_backend_google.backend import GoogleAsrBackend
from asr_core.audio import audio_bytes_to_temp_wav, looks_like_wav_bytes
from asr_core.models import AsrRequest


def _make_pcm_frames(frame_count: int = 1600) -> bytes:
    return b"\x01\x00" * frame_count


def _make_wav_bytes(path: Path, frames: bytes, sample_rate: int = 16000) -> bytes:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)
    return path.read_bytes()


def test_audio_bytes_to_temp_wav_wraps_raw_pcm(tmp_path: Path) -> None:
    raw_pcm = _make_pcm_frames()

    wav_path = audio_bytes_to_temp_wav(
        raw_pcm,
        sample_rate=16000,
        channels=1,
        sample_width=2,
        prefix="test_audio_",
    )

    written = Path(wav_path).read_bytes()
    assert looks_like_wav_bytes(written)
    with wave.open(wav_path, "rb") as wf:
        assert wf.getframerate() == 16000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.readframes(wf.getnframes()) == raw_pcm


def test_google_backend_extracts_pcm_from_wav_path(tmp_path: Path) -> None:
    wav_path = tmp_path / "speech.wav"
    raw_pcm = _make_pcm_frames()
    _make_wav_bytes(wav_path, raw_pcm)
    backend = GoogleAsrBackend(config={"credentials_json": "unused"}, client=object())

    content, sample_rate, duration = backend._request_audio(AsrRequest(wav_path=str(wav_path)))

    assert content == raw_pcm
    assert sample_rate == 16000
    assert 0.09 <= duration <= 0.11


def test_google_backend_accepts_raw_pcm_request_bytes() -> None:
    raw_pcm = _make_pcm_frames()
    backend = GoogleAsrBackend(config={"credentials_json": "unused"}, client=object())

    content, sample_rate, duration = backend._request_audio(
        AsrRequest(
            audio_bytes=raw_pcm,
            sample_rate=16000,
            metadata={"channels": 1, "encoding": "pcm_s16le", "sample_width_bytes": 2},
        )
    )

    assert content == raw_pcm
    assert sample_rate == 16000
    assert 0.09 <= duration <= 0.11


def test_google_backend_extracts_pcm_from_wav_bytes(tmp_path: Path) -> None:
    wav_path = tmp_path / "speech_bytes.wav"
    raw_pcm = _make_pcm_frames()
    wav_bytes = _make_wav_bytes(wav_path, raw_pcm)
    backend = GoogleAsrBackend(config={"credentials_json": "unused"}, client=object())

    content, sample_rate, duration = backend._request_audio(AsrRequest(audio_bytes=wav_bytes))

    assert content == raw_pcm
    assert sample_rate == 16000
    assert 0.09 <= duration <= 0.11
