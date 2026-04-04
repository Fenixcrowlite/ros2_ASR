from __future__ import annotations

import sys
import types

from asr_provider_base.models import ProviderAudio
from asr_provider_huggingface.http_client import HuggingFaceInferenceError


def _install_fake_transformers(monkeypatch, *, fail_first_timestamp_call: bool = False):
    captured: dict[str, object] = {"pipeline_calls": [], "empty_cache_calls": 0}

    class FakePipeline:
        def __call__(self, inputs, **kwargs):
            captured["pipeline_calls"].append({"inputs": inputs, "kwargs": dict(kwargs)})
            if fail_first_timestamp_call and len(captured["pipeline_calls"]) == 1:
                raise RuntimeError("timestamps unsupported")
            return {
                "text": "hello world",
                "chunks": [
                    {"text": "hello", "timestamp": (0.0, 0.4)},
                    {"text": "world", "timestamp": (0.41, 0.8)},
                ],
            }

    def fake_pipeline(**kwargs):
        captured["pipeline_init"] = dict(kwargs)
        return FakePipeline()

    fake_transformers = types.ModuleType("transformers")
    fake_transformers.pipeline = fake_pipeline

    fake_torch = types.ModuleType("torch")
    fake_torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    fake_torch.backends = types.SimpleNamespace(
        mps=types.SimpleNamespace(is_available=lambda: False)
    )
    fake_torch.float16 = "float16"
    fake_torch.float32 = "float32"
    fake_torch.bfloat16 = "bfloat16"
    fake_torch.cuda.empty_cache = lambda: captured.__setitem__(
        "empty_cache_calls",
        int(captured["empty_cache_calls"]) + 1,
    )

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    return captured


def test_huggingface_local_provider_runs_transformers_pipeline(
    monkeypatch,
    sample_wav: str,
) -> None:
    from asr_provider_huggingface.local_provider import HuggingFaceLocalProvider

    captured = _install_fake_transformers(monkeypatch, fail_first_timestamp_call=True)

    provider = HuggingFaceLocalProvider()
    provider.initialize(
        {
            "model_id": "openai/whisper-small",
            "device": "auto",
            "torch_dtype": "auto",
            "return_timestamps": "word",
        },
        {},
    )

    assert provider.validate_config() == []

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_local",
            request_id="req_local",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
            enable_word_timestamps=True,
        )
    )

    assert captured["pipeline_init"]["model"] == "openai/whisper-small"
    assert captured["pipeline_init"]["torch_dtype"] == "auto"
    assert result.provider_id == "huggingface_local"
    assert result.text == "hello world"
    assert result.timestamps_available is True
    assert [word.word for word in result.words] == ["hello", "world"]
    assert "timestamp_fallback" in result.tags
    assert provider.get_metrics().requests_total == 1
    assert provider.get_metadata().implementation == "transformers.pipeline"

    provider.teardown()
    assert captured["empty_cache_calls"] == 0


def test_huggingface_api_provider_normalizes_http_response(sample_wav: str) -> None:
    from asr_provider_huggingface.api_provider import HuggingFaceAPIProvider

    class FakeClient:
        def automatic_speech_recognition(self, **kwargs):
            assert kwargs["model_id"] == "openai/whisper-large-v3"
            assert kwargs["return_timestamps"] is True
            return {
                "text": "hello world",
                "chunks": [
                    {"text": "hello", "timestamp": [0.0, 0.4]},
                    {"text": "world", "timestamp": [0.41, 0.8]},
                ],
            }

    provider = HuggingFaceAPIProvider()
    provider.initialize(
        {
            "model_id": "openai/whisper-large-v3",
            "return_timestamps": True,
            "timeout_sec": 30.0,
        },
        {"HF_TOKEN": "hf_test_token"},
    )
    provider._client = FakeClient()

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_api",
            request_id="req_api",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
            enable_word_timestamps=True,
        )
    )

    assert result.provider_id == "huggingface_api"
    assert result.text == "hello world"
    assert result.timestamps_available is True
    assert [word.word for word in result.words] == ["hello", "world"]
    assert provider.get_metrics().requests_total == 1
    assert provider.get_status().state == "ready"


def test_huggingface_api_provider_surfaces_http_errors(sample_wav: str) -> None:
    from asr_provider_huggingface.api_provider import HuggingFaceAPIProvider

    class FailingClient:
        def automatic_speech_recognition(self, **kwargs):
            del kwargs
            raise HuggingFaceInferenceError(
                code="hf_auth_error",
                message="bad token",
                status_code=401,
            )

    provider = HuggingFaceAPIProvider()
    provider.initialize(
        {
            "model_id": "openai/whisper-large-v3",
        },
        {"HF_TOKEN": "hf_bad_token"},
    )
    provider._client = FailingClient()

    result = provider.recognize_once(
        ProviderAudio(
            session_id="session_api_error",
            request_id="req_api_error",
            language="en-US",
            sample_rate_hz=16000,
            wav_path=sample_wav,
            enable_word_timestamps=True,
        )
    )

    assert result.error_code == "hf_auth_error"
    assert result.degraded is True
    assert provider.get_status().state == "error"


def test_huggingface_api_provider_teardown_closes_http_client() -> None:
    from asr_provider_huggingface.api_provider import HuggingFaceAPIProvider

    closed = {"value": False}

    class FakeClient:
        def close(self) -> None:
            closed["value"] = True

    provider = HuggingFaceAPIProvider()
    provider._client = FakeClient()

    provider.teardown()

    assert closed["value"] is True
