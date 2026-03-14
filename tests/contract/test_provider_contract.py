from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from asr_provider_base.models import ProviderAudio


@dataclass
class DummyWord:
    word: str = "hello"
    start_sec: float = 0.0
    end_sec: float = 0.5
    confidence: float = 0.9


@dataclass
class DummyTimings:
    total_ms: float = 11.0
    postprocess_ms: float = 2.0


@dataclass
class DummyResponse:
    text: str = "hello world"
    confidence: float = 0.92
    language: str = "en-US"
    word_timestamps: list[DummyWord] = None  # type: ignore[assignment]
    timings: DummyTimings = field(default_factory=DummyTimings)
    success: bool = True
    error_code: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        if self.word_timestamps is None:
            self.word_timestamps = [DummyWord("hello", 0.0, 0.4), DummyWord("world", 0.41, 0.8)]


class DeterministicWhisperBackend:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def recognize_once(self, request: Any) -> DummyResponse:
        del request
        return DummyResponse()

    def streaming_recognize(self, chunks: list[bytes], language: str, sample_rate: int) -> DummyResponse:
        del chunks, sample_rate
        return DummyResponse(text=f"streamed {language}")


class FailingWhisperBackend(DeterministicWhisperBackend):
    def recognize_once(self, request: Any) -> DummyResponse:
        del request
        return DummyResponse(success=False, error_code="whisper_model_error", error_message="simulated failure")

    def streaming_recognize(self, chunks: list[bytes], language: str, sample_rate: int) -> DummyResponse:
        del chunks, language, sample_rate
        return DummyResponse(success=False, error_code="whisper_runtime_error", error_message="simulated failure")


class EmptyWhisperBackend(DeterministicWhisperBackend):
    def recognize_once(self, request: Any) -> DummyResponse:
        del request
        return DummyResponse(text="", word_timestamps=[])


class DeterministicAzureBackend:
    def __init__(self, config: dict[str, Any]) -> None:
        self.key = config.get("speech_key", "")
        self.region = config.get("region", "")

    def recognize_once(self, request: Any) -> DummyResponse:
        del request
        return DummyResponse(text="azure transcript")


def _assert_common_result_contract(result: Any, provider_id: str) -> None:
    assert result.provider_id == provider_id
    assert result.request_id
    assert result.session_id
    assert isinstance(result.text, str)
    assert result.is_final is True
    assert isinstance(result.confidence_available, bool)
    assert isinstance(result.timestamps_available, bool)
    assert isinstance(result.latency.total_ms, float)


def test_whisper_provider_contract(monkeypatch: pytest.MonkeyPatch, sample_wav: str) -> None:
    import asr_provider_whisper.whisper_provider as whisper_module

    monkeypatch.setattr(whisper_module, "WhisperAsrBackend", DeterministicWhisperBackend)

    provider = whisper_module.WhisperProvider()
    provider.initialize({"model_size": "tiny", "device": "cpu"}, {})

    assert provider.validate_config() == []
    caps = provider.discover_capabilities()
    assert caps.supports_streaming is True
    assert caps.requires_network is False

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_1",
            request_id="req_1",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
            enable_word_timestamps=True,
        )
    )
    _assert_common_result_contract(result, "whisper")

    provider.start_stream({"language": "en-US", "sample_rate_hz": 16000})
    provider.push_audio(b"chunk-1")
    stream_result = provider.stop_stream()
    _assert_common_result_contract(stream_result, "whisper")
    assert provider.get_status().state == "ready"

    provider.teardown()
    assert provider.get_status().state == "stopped"


def test_whisper_provider_contract_reports_backend_failure_honestly(
    monkeypatch: pytest.MonkeyPatch, sample_wav: str
) -> None:
    import asr_provider_whisper.whisper_provider as whisper_module

    monkeypatch.setattr(whisper_module, "WhisperAsrBackend", FailingWhisperBackend)

    provider = whisper_module.WhisperProvider()
    provider.initialize({"model_size": "tiny", "device": "cpu"}, {})

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_1",
            request_id="req_1",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
        )
    )

    assert result.text == "hello world"
    assert result.error_code == "whisper_model_error"
    assert result.degraded is True


def test_whisper_provider_contract_marks_empty_transcript_as_degraded(
    monkeypatch: pytest.MonkeyPatch, sample_wav: str
) -> None:
    import asr_provider_whisper.whisper_provider as whisper_module

    monkeypatch.setattr(whisper_module, "WhisperAsrBackend", EmptyWhisperBackend)

    provider = whisper_module.WhisperProvider()
    provider.initialize({"model_size": "tiny", "device": "cpu"}, {})

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_1",
            request_id="req_1",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
        )
    )

    assert result.text == ""
    assert result.degraded is True
    assert result.error_code == "empty_transcript"
    assert result.raw_metadata_ref == "provider:whisper_empty"


def test_azure_provider_contract(monkeypatch: pytest.MonkeyPatch, sample_wav: str) -> None:
    import asr_provider_azure.azure_provider as azure_module

    monkeypatch.setattr(azure_module, "AzureAsrBackend", DeterministicAzureBackend)

    provider = azure_module.AzureProvider()
    provider.initialize({"region": "eastus"}, {"AZURE_SPEECH_KEY": "secret", "AZURE_SPEECH_REGION": "eastus"})

    assert provider.validate_config() == []
    caps = provider.discover_capabilities()
    assert caps.requires_network is True
    assert caps.supports_streaming is False

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_azure",
            request_id="req_azure",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
        )
    )
    _assert_common_result_contract(result, "azure")

    provider.start_stream()
    unsupported = provider.stop_stream()
    assert unsupported.degraded is True
    assert unsupported.error_code == "unsupported"


def test_azure_provider_validation_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    import asr_provider_azure.azure_provider as azure_module

    monkeypatch.setattr(azure_module, "AzureAsrBackend", DeterministicAzureBackend)
    provider = azure_module.AzureProvider()
    provider.initialize({"region": ""}, {})

    errors = provider.validate_config()
    assert "Azure speech key is missing" in errors
    assert "Azure region is missing" in errors
