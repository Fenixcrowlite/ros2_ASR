from __future__ import annotations

import uuid

import pytest

from web_gui.app.aws_auth_store import (
    auth_profile_path,
    parse_env_like_text,
    resolve_auth_context,
    save_auth_profile,
)


def test_parse_env_like_text_parses_key_value_rows() -> None:
    raw = """
# comment
AWS_PROFILE=ros2ws
AWS_REGION=eu-north-1
AWS_S3_BUCKET=bucket-demo
"""
    values = parse_env_like_text(raw)
    assert values["AWS_PROFILE"] == "ros2ws"
    assert values["AWS_REGION"] == "eu-north-1"
    assert values["AWS_S3_BUCKET"] == "bucket-demo"


def test_resolve_auth_context_sso_writes_runtime_files() -> None:
    name = f"unit_auth_{uuid.uuid4().hex[:8]}"
    path = auth_profile_path(name)
    if path.exists():
        path.unlink()
    try:
        save_auth_profile(
            name,
            values={
                "AWS_AUTH_TYPE": "sso",
                "AWS_PROFILE": "ros2ws",
                "AWS_REGION": "eu-north-1",
                "AWS_SSO_START_URL": "https://d-example.awsapps.com/start",
                "AWS_SSO_REGION": "eu-north-1",
                "AWS_SSO_ACCOUNT_ID": "123456789012",
                "AWS_SSO_ROLE_NAME": "AdministratorAccess",
                "AWS_S3_BUCKET": "bucket-demo",
            },
        )
        ctx = resolve_auth_context(name)
        assert ctx.profile_name == "ros2ws"
        assert ctx.runtime_secrets["aws_profile"] == "ros2ws"
        assert ctx.runtime_secrets["aws_region"] == "eu-north-1"
        assert ctx.runtime_secrets["aws_s3_bucket"] == "bucket-demo"
        assert "AWS_CONFIG_FILE" in ctx.env_extra
        assert "AWS_SHARED_CREDENTIALS_FILE" in ctx.env_extra
        assert ctx.env_extra["AWS_SDK_LOAD_CONFIG"] == "1"
    finally:
        if path.exists():
            path.unlink()


def test_resolve_auth_context_sso_runtime_requires_account_and_role() -> None:
    name = f"unit_auth_{uuid.uuid4().hex[:8]}"
    path = auth_profile_path(name)
    if path.exists():
        path.unlink()
    try:
        save_auth_profile(
            name,
            values={
                "AWS_AUTH_TYPE": "sso",
                "AWS_PROFILE": "ros2ws",
                "AWS_REGION": "eu-north-1",
                "AWS_SSO_START_URL": "https://d-example.awsapps.com/start",
                "AWS_SSO_REGION": "eu-north-1",
            },
        )
        with pytest.raises(ValueError, match="AWS_SSO_ACCOUNT_ID and AWS_SSO_ROLE_NAME"):
            resolve_auth_context(name)

        login_ctx = resolve_auth_context(name, for_login=True)
        assert "AWS_CONFIG_FILE" in login_ctx.env_extra
        assert login_ctx.env_extra["AWS_SDK_LOAD_CONFIG"] == "1"
    finally:
        if path.exists():
            path.unlink()
