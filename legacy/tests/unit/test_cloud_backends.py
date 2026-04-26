import os

import pytest
from asr_backend_aws.backend import AwsAsrBackend
from asr_backend_azure.backend import AzureAsrBackend
from asr_backend_google.backend import GoogleAsrBackend
from asr_core.models import AsrRequest


@pytest.mark.cloud
def test_google_cloud_integration_or_skip(sample_wav: str) -> None:
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        pytest.skip("Google credentials are not configured")
    backend = GoogleAsrBackend(config={"model": "latest_long"})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk-SK"))
    assert response.error_code != "credential_missing"


@pytest.mark.cloud
def test_aws_cloud_integration_or_skip(sample_wav: str) -> None:
    if not (
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    ) and not os.getenv("AWS_PROFILE"):
        pytest.skip("AWS credentials/profile are not configured")
    if not os.getenv("ASR_AWS_S3_BUCKET"):
        pytest.skip("ASR_AWS_S3_BUCKET is required")
    backend = AwsAsrBackend(config={"region": os.getenv("AWS_REGION", "us-east-1")})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk-SK"))
    assert response.error_code not in {"credential_missing", "config_missing"}


@pytest.mark.cloud
def test_azure_cloud_integration_or_skip(sample_wav: str) -> None:
    if not (os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION")):
        pytest.skip("Azure credentials are not configured")
    backend = AzureAsrBackend(config={})
    response = backend.recognize_once(AsrRequest(wav_path=sample_wav, language="sk-SK"))
    assert response.error_code != "credential_missing"
