from __future__ import annotations

from asr_backend_azure.backend import _build_speech_config


class _FakeSpeechConfig:
    def __init__(self, *, subscription=None, region=None, endpoint=None, **kwargs) -> None:
        del kwargs
        self.subscription = subscription
        self.region = region
        self.endpoint = endpoint
        self.properties: list[tuple[str, str]] = []
        self.speech_recognition_language = ""
        self.output_format = None
        self.word_timestamps_requested = False

    def request_word_level_timestamps(self) -> None:
        self.word_timestamps_requested = True

    def set_property(self, key, value) -> None:
        self.properties.append((key, value))


class _FakeSpeechSdk:
    class PropertyId:
        SpeechServiceConnection_EndpointId = "SpeechServiceConnection_EndpointId"

    class OutputFormat:
        Detailed = "Detailed"

    SpeechConfig = _FakeSpeechConfig


def test_build_speech_config_uses_endpoint_url_directly() -> None:
    sdk = _FakeSpeechSdk()
    config = _build_speech_config(
        sdk,
        key="key",
        region="westeurope",
        endpoint="https://westeurope.api.cognitive.microsoft.com/",
        language="en-US",
    )

    assert config.endpoint == "https://westeurope.api.cognitive.microsoft.com/"
    assert config.region is None
    assert config.properties == []
    assert config.speech_recognition_language == "en-US"
    assert config.word_timestamps_requested is True


def test_build_speech_config_uses_endpoint_id_as_property() -> None:
    sdk = _FakeSpeechSdk()
    config = _build_speech_config(
        sdk,
        key="key",
        region="westeurope",
        endpoint="custom-endpoint-id",
        language="en-US",
    )

    assert config.endpoint is None
    assert config.region == "westeurope"
    assert config.properties == [("SpeechServiceConnection_EndpointId", "custom-endpoint-id")]
