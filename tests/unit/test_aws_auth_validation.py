from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

import asr_backend_aws.backend as aws_backend_module
from asr_backend_aws.backend import AwsAsrBackend


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_aws_auth_validation_reports_expired_sso_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write(
        tmp_path / ".aws" / "config",
        """
[sso-session ros2ws-sso]
sso_start_url = https://example.awsapps.com/start
sso_region = eu-north-1

[profile ros2ws]
sso_session = ros2ws-sso
region = eu-north-1
output = json
""".strip(),
    )
    _write(
        tmp_path / ".aws" / "sso" / "cache" / "token.json",
        """
{"accessToken":"token","startUrl":"https://example.awsapps.com/start","region":"eu-north-1","expiresAt":"2026-03-09T15:56:33Z"}
""".strip(),
    )

    backend = AwsAsrBackend(config={"profile": "ros2ws", "region": "eu-north-1"})
    errors = backend.auth_validation_errors()

    assert errors
    assert "expired" in errors[0].lower()
    assert "aws sso login --profile ros2ws" in errors[0]


def test_aws_auth_validation_accepts_unexpired_sso_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write(
        tmp_path / ".aws" / "config",
        """
[sso-session ros2ws-sso]
sso_start_url = https://example.awsapps.com/start
sso_region = eu-north-1

[profile ros2ws]
sso_session = ros2ws-sso
region = eu-north-1
output = json
""".strip(),
    )
    _write(
        tmp_path / ".aws" / "sso" / "cache" / "token.json",
        """
{"accessToken":"token","startUrl":"https://example.awsapps.com/start","region":"eu-north-1","expiresAt":"2026-06-09T15:56:33Z"}
""".strip(),
    )

    backend = AwsAsrBackend(config={"profile": "ros2ws", "region": "eu-north-1"})
    assert backend.auth_validation_errors() == []


def test_aws_auth_validation_accepts_valid_cli_cache_when_sso_token_is_expired(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write(
        tmp_path / ".aws" / "config",
        """
[sso-session ros2ws-sso]
sso_start_url = https://example.awsapps.com/start
sso_region = eu-north-1

[profile ros2ws]
sso_session = ros2ws-sso
sso_account_id = 123456789012
region = eu-north-1
output = json
""".strip(),
    )
    _write(
        tmp_path / ".aws" / "sso" / "cache" / "token.json",
        """
{"accessToken":"token","startUrl":"https://example.awsapps.com/start","region":"eu-north-1","expiresAt":"2026-03-09T15:56:33Z"}
""".strip(),
    )
    _write(
        tmp_path / ".aws" / "cli" / "cache" / "role.json",
        """
{"ProviderType":"sso","Credentials":{"AccessKeyId":"ASIA...","SecretAccessKey":"secret","SessionToken":"token","Expiration":"2026-06-10T09:17:43Z","AccountId":"123456789012"}}
""".strip(),
    )

    backend = AwsAsrBackend(config={"profile": "ros2ws", "region": "eu-north-1"})
    status = backend.auth_status()
    assert backend.auth_validation_errors() == []
    assert status["status"] == "role_credentials_valid_sso_expired"
    assert status["runtime_ready"] is True
    assert status["login_recommended"] is True


def test_aws_clients_use_valid_cli_cache_credentials_before_sso_refresh(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    _write(
        tmp_path / ".aws" / "config",
        """
[sso-session ros2ws-sso]
sso_start_url = https://example.awsapps.com/start
sso_region = eu-north-1

[profile ros2ws]
sso_session = ros2ws-sso
sso_account_id = 123456789012
region = eu-north-1
output = json
""".strip(),
    )
    _write(
        tmp_path / ".aws" / "cli" / "cache" / "role.json",
        """
{"ProviderType":"sso","Credentials":{"AccessKeyId":"ASIAEXAMPLE","SecretAccessKey":"secret","SessionToken":"token","Expiration":"2026-06-10T09:17:43Z","AccountId":"123456789012"}}
""".strip(),
    )

    calls: list[dict[str, str]] = []

    class _FakeSession:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def client(self, name: str, region_name: str | None = None):
            return {"name": name, "region_name": region_name}

    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(Session=_FakeSession))

    backend = AwsAsrBackend(config={"profile": "ros2ws", "region": "eu-north-1", "s3_bucket": "dummy"})
    s3, transcribe = backend._clients()

    assert calls
    assert calls[0]["aws_access_key_id"] == "ASIAEXAMPLE"
    assert calls[0]["aws_secret_access_key"] == "secret"
    assert calls[0]["aws_session_token"] == "token"
    assert calls[0]["region_name"] == "eu-north-1"
    assert s3["name"] == "s3"
    assert transcribe["name"] == "transcribe"


def test_aws_create_stream_session_uses_streaming_region_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class _FakeStreamingSession:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    backend = AwsAsrBackend(
        config={
            "profile": "ros2ws",
            "region": "eu-north-1",
            "streaming_region": "eu-central-1",
            "s3_bucket": "dummy",
        }
    )
    monkeypatch.setattr(backend, "auth_validation_errors", lambda: [])
    monkeypatch.setattr(backend, "_streaming_credential_resolver", lambda: "resolver")
    monkeypatch.setattr(aws_backend_module, "AwsStreamingSession", _FakeStreamingSession)

    backend.create_stream_session(language="en-US", sample_rate=16000)

    assert calls
    assert calls[0]["region"] == "eu-central-1"


def test_aws_streaming_endpoint_validation_reports_unresolvable_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        aws_backend_module.socket,
        "getaddrinfo",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            aws_backend_module.socket.gaierror(-2, "Name or service not known")
        ),
    )

    with pytest.raises(RuntimeError, match="transcribestreaming.eu-north-1.amazonaws.com"):
        aws_backend_module._ensure_streaming_endpoint_resolves("eu-north-1")


def test_aws_streaming_session_classifies_dns_resolution_failure() -> None:
    error_code, _ = aws_backend_module.AwsStreamingSession._classify_error(
        RuntimeError("AWS_IO_DNS_INVALID_NAME: Host name was invalid for dns resolution.")
    )

    assert error_code == "aws_stream_endpoint_unreachable"


def test_aws_streaming_session_id_matches_aws_uuid_constraints() -> None:
    session_id = aws_backend_module._aws_streaming_session_id()

    assert len(session_id) == 36
    assert str(uuid.UUID(session_id)) == session_id
