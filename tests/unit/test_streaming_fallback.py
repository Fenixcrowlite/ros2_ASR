from __future__ import annotations

import io
import wave

import pytest
from asr_core.audio import pcm_chunks_to_wav_bytes
from asr_core.backend import AsrBackend
from asr_core.models import AsrRequest, AsrResponse, AsrTimings


class _ProbeBackend(AsrBackend):
    def __init__(self) -> None:
        super().__init__()
        self.last_request: AsrRequest | None = None

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        self.last_request = request
        return AsrResponse(
            text="ok",
            language=request.language,
            backend_info={"provider": "probe", "model": "probe", "region": "local"},
            timings=AsrTimings(preprocess_ms=2.0, inference_ms=3.0, postprocess_ms=4.0),
            audio_duration_sec=0.2,
            success=True,
        )


def test_pcm_chunks_to_wav_bytes_wraps_pcm_chunks_into_wav() -> None:
    chunks = [b"\x00\x00" * 1600, b"\x01\x00" * 1600]
    wav_bytes = pcm_chunks_to_wav_bytes(chunks, sample_rate=16000)

    assert wav_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getframerate() == 16000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getnframes() == 3200


def test_backend_streaming_requires_explicit_implementation() -> None:
    backend = _ProbeBackend()

    with pytest.raises(NotImplementedError, match="does not support streaming_recognize"):
        backend.streaming_recognize([b"\x00\x00" * 1600], language="en-US", sample_rate=16000)
