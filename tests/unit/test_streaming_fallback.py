from __future__ import annotations

import io
import wave

from asr_core.backend import AsrBackend
from asr_core.models import AsrRequest, AsrResponse, AsrTimings


class _FallbackProbeBackend(AsrBackend):
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


def test_streaming_fallback_wraps_pcm_chunks_into_wav() -> None:
    backend = _FallbackProbeBackend()
    chunks = [b"\x00\x00" * 1600, b"\x01\x00" * 1600]

    response = backend.streaming_recognize(chunks, language="en-US", sample_rate=16000)

    assert backend.last_request is not None
    assert backend.last_request.audio_bytes is not None
    assert backend.last_request.audio_bytes.startswith(b"RIFF")
    with wave.open(io.BytesIO(backend.last_request.audio_bytes), "rb") as wf:
        assert wf.getframerate() == 16000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getnframes() == 3200
    assert response.success
    assert response.backend_info["streaming_fallback"] == "true"
