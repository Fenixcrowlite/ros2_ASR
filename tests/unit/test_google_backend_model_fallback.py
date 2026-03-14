from __future__ import annotations

from pathlib import Path

from asr_backend_google.backend import GoogleAsrBackend
from asr_core.models import AsrRequest


class _FakeSpeechModule:
    class RecognitionConfig:
        class AudioEncoding:
            LINEAR16 = "LINEAR16"

        def __init__(self, **kwargs):
            self.model = kwargs.get("model", "")

    class RecognitionAudio:
        def __init__(self, *, content: bytes):
            self.content = content


class _FakeAlt:
    def __init__(self, transcript: str):
        self.transcript = transcript
        self.confidence = 0.95
        self.words: list[object] = []


class _FakeResult:
    def __init__(self, transcript: str):
        self.alternatives = [_FakeAlt(transcript)]


class _FakeResponse:
    def __init__(self, transcript: str):
        self.results = [_FakeResult(transcript)]


class _FakeClient:
    def __init__(self) -> None:
        self.models: list[str] = []

    def recognize(self, *, config, audio):  # noqa: ANN001
        del audio
        self.models.append(str(getattr(config, "model", "")))
        if str(getattr(config, "model", "")) == "latest_long":
            raise RuntimeError(
                "400 Invalid recognition 'config': "
                "The requested model is currently not supported for language : sk-SK."
            )
        return _FakeResponse("ahoj svet")


def test_google_backend_falls_back_to_default_model_for_unsupported_language(
    tmp_path: Path,
) -> None:
    creds = tmp_path / "gcp.json"
    creds.write_text("{}", encoding="utf-8")
    client = _FakeClient()

    backend = GoogleAsrBackend(
        config={"credentials_json": str(creds), "model": "latest_long", "region": "global"},
        client=client,
    )
    backend._speech = _FakeSpeechModule

    response = backend.recognize_once(
        AsrRequest(
            wav_path="data/sample/en_hello.wav",
            language="sk-SK",
            enable_word_timestamps=False,
        )
    )

    assert response.success is True
    assert response.backend_info.get("requested_model") == "latest_long"
    assert response.backend_info.get("model") == "default"
    assert client.models == ["latest_long", "default"]
