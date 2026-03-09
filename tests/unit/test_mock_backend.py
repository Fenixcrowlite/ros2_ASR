from asr_backend_mock.backend import MockAsrBackend
from asr_core.models import AsrRequest


def test_mock_backend_recognize_once(sample_wav: str) -> None:
    backend = MockAsrBackend(config={"transcript_map": {"en_hello.wav": "hello world"}})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="en-US"))

    assert response.success
    assert response.text == "hello world"
    assert response.confidence > 0.0
    assert response.audio_duration_sec > 0.0
    assert response.timings.total_ms > 0.0


def test_mock_backend_streaming() -> None:
    backend = MockAsrBackend(config={})
    response = backend.streaming_recognize(
        chunks=[b"a" * 1000, b"b" * 1000],
        language="en-US",
        sample_rate=16000,
    )
    assert response.success
    assert response.text
    assert len(response.partials) == 2


def test_mock_backend_returns_file_missing_for_unknown_wav() -> None:
    backend = MockAsrBackend(config={})
    response = backend.recognize_once(
        AsrRequest(wav_path="data/sample/does_not_exist.wav", language="en-US")
    )
    assert not response.success
    assert response.error_code == "file_missing"
