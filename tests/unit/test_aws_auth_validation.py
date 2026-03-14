from __future__ import annotations

from pathlib import Path

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
