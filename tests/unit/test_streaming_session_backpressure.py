from __future__ import annotations

import asr_backend_aws.backend as aws_backend_module
import asr_backend_google.backend as google_backend_module


class _IdleThread:
    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs

    def start(self) -> None:
        return None

    def join(self, timeout: float | None = None) -> None:
        del timeout
        return None

    def is_alive(self) -> bool:
        return False


def test_aws_streaming_session_drops_oldest_audio_when_queue_is_full(monkeypatch) -> None:
    monkeypatch.setattr(aws_backend_module.threading, "Thread", _IdleThread)

    session = aws_backend_module.AwsStreamingSession(
        region="us-east-1",
        credential_resolver="resolver",
        language="en-US",
        sample_rate=16000,
    )

    chunks = [
        bytes([idx]) * 320 for idx in range(aws_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE + 2)
    ]
    for chunk in chunks:
        session.push_audio(chunk)

    assert session._audio_queue.maxsize == aws_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE
    assert session._audio_queue.qsize() == aws_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE
    assert list(session._audio_queue.queue) == chunks[2:]


def test_google_streaming_session_drops_oldest_audio_when_queue_is_full(monkeypatch) -> None:
    monkeypatch.setattr(google_backend_module.threading, "Thread", _IdleThread)

    class _SpeechModule:
        class StreamingRecognitionConfig:
            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs

        class RecognitionConfig:
            class AudioEncoding:
                LINEAR16 = "LINEAR16"

            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs

        class StreamingRecognizeRequest:
            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs

    session = google_backend_module.GoogleStreamingSession(
        client=object(),
        speech_module=_SpeechModule,
        language="en-US",
        sample_rate=16000,
    )

    chunks = [
        bytes([idx]) * 320 for idx in range(google_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE + 2)
    ]
    for chunk in chunks:
        session.push_audio(chunk)

    assert session._audio_queue.maxsize == google_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE
    assert session._audio_queue.qsize() == google_backend_module.STREAMING_AUDIO_QUEUE_MAXSIZE
    assert list(session._audio_queue.queue) == chunks[2:]
