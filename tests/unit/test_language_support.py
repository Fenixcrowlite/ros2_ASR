from __future__ import annotations

from asr_backend_aws.backend import AwsAsrBackend
from asr_backend_azure.backend import AzureAsrBackend
from asr_backend_google.backend import GoogleAsrBackend
from asr_backend_mock.backend import MockAsrBackend
from asr_backend_vosk.backend import VoskAsrBackend
from asr_backend_whisper.backend import WhisperAsrBackend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest
from asr_provider_whisper.whisper_provider import WhisperProvider


def test_normalize_language_code_slovak_variants() -> None:
    assert normalize_language_code("sk", fallback="en-US") == "sk-SK"
    assert normalize_language_code("SK-sk", fallback="en-US") == "sk-SK"
    assert normalize_language_code("sk_sk", fallback="en-US") == "sk-SK"
    assert normalize_language_code("sk-SK", fallback="en-US") == "sk-SK"


def test_mock_backend_supports_slovak_language(sample_wav: str) -> None:
    backend = MockAsrBackend(config={})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert response.success
    assert response.language == "sk-SK"


def test_vosk_backend_normalizes_slovak_when_model_missing(sample_wav: str) -> None:
    backend = VoskAsrBackend(config={})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert not response.success
    assert response.error_code == "vosk_model_missing"
    assert response.language == "sk-SK"


def test_whisper_backend_normalizes_slovak_on_model_error(
    sample_wav: str, monkeypatch
) -> None:
    backend = WhisperAsrBackend(
        config={"model_size": "tiny", "device": "cpu", "compute_type": "int8"}
    )
    monkeypatch.setattr(backend, "_load_model", lambda: False)
    backend._load_error = "test_error"
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert not response.success
    assert response.error_code == "whisper_model_error"
    assert response.language == "sk-SK"


def test_whisper_provider_rejects_legacy_cpu_fallback_flag() -> None:
    provider = WhisperProvider()
    provider.initialize({"device": "cuda", "allow_cpu_fallback": True}, credentials_ref={})
    assert provider.validate_config() == [
        "Whisper setting `allow_cpu_fallback` is no longer supported. "
        "Fix CUDA runtime libraries or set device=cpu explicitly."
    ]


def test_google_backend_normalizes_slovak_on_credential_error(
    sample_wav: str, monkeypatch
) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    backend = GoogleAsrBackend(config={"credentials_json": ""})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert not response.success
    assert response.error_code == "credential_missing"
    assert response.language == "sk-SK"


def test_aws_backend_normalizes_slovak_on_credential_error(sample_wav: str, monkeypatch) -> None:
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    backend = AwsAsrBackend(config={"region": "us-east-1", "s3_bucket": "dummy", "cleanup": False})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert not response.success
    assert response.error_code == "credential_missing"
    assert response.language == "sk-SK"


def test_azure_backend_normalizes_slovak_on_credential_error(
    sample_wav: str, monkeypatch
) -> None:
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)
    backend = AzureAsrBackend(config={"speech_key": "", "region": ""})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk"))
    assert not response.success
    assert response.error_code == "credential_missing"
    assert response.language == "sk-SK"
