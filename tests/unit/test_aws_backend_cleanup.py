from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from asr_backend_aws.backend import AwsAsrBackend
from asr_core.models import AsrRequest


class FakeAwsSession:
    def __init__(self, *, s3: MagicMock, transcribe: MagicMock) -> None:
        self._s3 = s3
        self._transcribe = transcribe

    def client(self, name: str, region_name: str | None = None) -> MagicMock:
        if name == "s3":
            return self._s3
        if name == "transcribe":
            return self._transcribe
        raise ValueError(f"Unsupported client: {name}")


def _make_backend(s3: MagicMock, transcribe: MagicMock) -> AwsAsrBackend:
    session = FakeAwsSession(s3=s3, transcribe=transcribe)
    return AwsAsrBackend(
        config={
            "region": "us-east-1",
            "s3_bucket": "unit-test-bucket",
            "access_key_id": "dummy",
            "secret_access_key": "dummy",
            "cleanup": True,
        },
        client=session,
    )


def test_aws_cleanup_on_success(sample_wav: str, monkeypatch) -> None:
    s3 = MagicMock()
    transcribe = MagicMock()
    transcribe.get_transcription_job.return_value = {
        "TranscriptionJob": {
            "TranscriptionJobStatus": "COMPLETED",
            "Transcript": {"TranscriptFileUri": "https://example.com/transcript.json"},
        }
    }

    backend = _make_backend(s3=s3, transcribe=transcribe)

    monkeypatch.setattr("asr_backend_aws.backend.time.sleep", lambda _: None)
    monkeypatch.setattr(
        "asr_backend_aws.backend.requests.get",
        lambda *_args, **_kwargs: SimpleNamespace(
            json=lambda: {
                "results": {
                    "transcripts": [{"transcript": "hello world"}],
                    "items": [],
                }
            }
        ),
    )

    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="en-US"))

    assert response.success
    assert transcribe.delete_transcription_job.call_count == 1
    assert s3.delete_object.call_count == 1
    assert s3.delete_object.call_args.kwargs["Bucket"] == "unit-test-bucket"


def test_aws_cleanup_on_error(sample_wav: str, monkeypatch) -> None:
    s3 = MagicMock()
    transcribe = MagicMock()
    transcribe.get_transcription_job.return_value = {
        "TranscriptionJob": {
            "TranscriptionJobStatus": "COMPLETED",
            "Transcript": {"TranscriptFileUri": "https://example.com/transcript.json"},
        }
    }

    backend = _make_backend(s3=s3, transcribe=transcribe)

    monkeypatch.setattr("asr_backend_aws.backend.time.sleep", lambda _: None)

    def raise_download_error(*_args, **_kwargs):
        raise RuntimeError("download failed")

    monkeypatch.setattr("asr_backend_aws.backend.requests.get", raise_download_error)

    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="en-US"))

    assert not response.success
    assert response.error_code == "aws_runtime_error"
    assert transcribe.delete_transcription_job.call_count == 1
    assert s3.delete_object.call_count == 1
