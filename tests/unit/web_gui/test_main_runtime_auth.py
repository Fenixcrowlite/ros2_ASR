from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

import web_gui.app.main as gui_main


def test_validate_cloud_auth_google_requires_credentials_file() -> None:
    payload = {"model_runs": "google:latest_long"}
    merged_cfg = {"asr": {"backend": "google"}, "backends": {"google": {}}}
    env_merged: dict[str, str] = {}

    with pytest.raises(HTTPException, match="Google backend selected but credentials are missing"):
        gui_main._validate_cloud_auth(  # noqa: SLF001
            payload=payload,
            merged_cfg=merged_cfg,
            env_merged=env_merged,
        )


def test_validate_cloud_auth_azure_requires_key_and_region() -> None:
    payload = {"model_runs": "azure:speech"}
    merged_cfg = {"asr": {"backend": "azure"}, "backends": {"azure": {"region": "westeurope"}}}
    env_merged: dict[str, str] = {}

    with pytest.raises(HTTPException, match="Azure backend selected but auth is incomplete"):
        gui_main._validate_cloud_auth(  # noqa: SLF001
            payload=payload,
            merged_cfg=merged_cfg,
            env_merged=env_merged,
        )


def test_validate_cloud_auth_aws_sets_sdk_load_config_and_runs_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aws_config"
    creds_path = tmp_path / "aws_credentials"
    config_path.write_text("[default]\nregion = us-east-1\n", encoding="utf-8")
    creds_path.write_text("", encoding="utf-8")

    payload = {"model_runs": "aws:transcribe"}
    merged_cfg = {"asr": {"backend": "aws"}, "backends": {"aws": {"s3_bucket": "demo-bucket"}}}
    env_merged = {
        "AWS_PROFILE": "ros2ws",
        "ASR_AWS_S3_BUCKET": "demo-bucket",
        "AWS_CONFIG_FILE": str(config_path),
        "AWS_SHARED_CREDENTIALS_FILE": str(creds_path),
    }
    called: list[str] = []

    monkeypatch.setattr(gui_main, "_aws_sts_preflight_enabled", lambda: True)
    monkeypatch.setattr(gui_main, "_run_aws_sts_preflight", lambda _env: called.append("ok"))

    gui_main._validate_cloud_auth(  # noqa: SLF001
        payload=payload,
        merged_cfg=merged_cfg,
        env_merged=env_merged,
    )

    assert env_merged["AWS_SDK_LOAD_CONFIG"] == "1"
    assert called == ["ok"]


def test_validate_cloud_auth_uses_explicit_targets_over_default_backend() -> None:
    payload = {"model_runs": "mock"}
    merged_cfg = {
        "asr": {"backend": "aws"},
        "backends": {"aws": {"s3_bucket": "demo-bucket"}},
    }
    env_merged: dict[str, str] = {}

    # No exception expected: explicit target is mock, cloud auth must not be enforced.
    gui_main._validate_cloud_auth(  # noqa: SLF001
        payload=payload,
        merged_cfg=merged_cfg,
        env_merged=env_merged,
    )


def test_validate_cloud_auth_google_rejects_non_json_credentials_file(tmp_path: Path) -> None:
    bad_creds = tmp_path / "google_credentials.json"
    bad_creds.write_text("{bad-json", encoding="utf-8")

    payload = {"model_runs": "google:latest_long"}
    merged_cfg = {"asr": {"backend": "google"}, "backends": {"google": {}}}
    env_merged = {"GOOGLE_APPLICATION_CREDENTIALS": str(bad_creds)}

    with pytest.raises(HTTPException, match="Google credentials file is not valid JSON"):
        gui_main._validate_cloud_auth(  # noqa: SLF001
            payload=payload,
            merged_cfg=merged_cfg,
            env_merged=env_merged,
        )


def test_run_aws_sts_preflight_falls_back_to_cli_when_boto3_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def _raise_missing(_env: dict[str, str]) -> None:
        raise ModuleNotFoundError("No module named boto3")

    monkeypatch.setattr(gui_main, "_run_aws_sts_preflight_boto3", _raise_missing)
    monkeypatch.setattr(gui_main, "_run_aws_sts_preflight_cli", lambda _env: called.append("cli"))

    gui_main._run_aws_sts_preflight({})  # noqa: SLF001

    assert called == ["cli"]


def test_normalize_aws_auth_error_maps_expired_pending_authorization() -> None:
    detail = (
        "aws: [ERROR]: The pending authorization to retrieve an SSO token has expired. "
        "The login flow to retrieve an SSO token must be restarted."
    )

    normalized = gui_main._normalize_aws_auth_error(detail)  # noqa: SLF001

    assert "AWS SSO authorization expired before completion" in normalized


def test_normalize_aws_auth_error_maps_missing_sso_token() -> None:
    detail = "Error loading SSO Token: Token for ros2ws_sso-sso does not exist"

    normalized = gui_main._normalize_aws_auth_error(detail)  # noqa: SLF001

    assert "AWS SSO token is not present locally" in normalized


def test_run_aws_sts_preflight_uses_ttl_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(gui_main, "_AWS_STS_PREFLIGHT_CACHE", {})
    monkeypatch.setattr(gui_main, "_aws_sts_preflight_ttl_sec", lambda: 120.0)
    monkeypatch.setattr(
        gui_main,
        "_run_aws_sts_preflight_boto3",
        lambda _env: calls.append("boto3"),
    )

    env_merged = {
        "AWS_PROFILE": "ros2ws",
        "AWS_REGION": "eu-north-1",
        "ASR_AWS_S3_BUCKET": "demo-bucket",
    }
    gui_main._run_aws_sts_preflight(env_merged)  # noqa: SLF001
    gui_main._run_aws_sts_preflight(env_merged)  # noqa: SLF001

    assert calls == ["boto3"]


def test_run_aws_sts_preflight_cache_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(gui_main, "_AWS_STS_PREFLIGHT_CACHE", {})
    monkeypatch.setattr(gui_main, "_aws_sts_preflight_ttl_sec", lambda: 0.0)
    monkeypatch.setattr(
        gui_main,
        "_run_aws_sts_preflight_boto3",
        lambda _env: calls.append("boto3"),
    )

    env_merged = {
        "AWS_PROFILE": "ros2ws",
        "AWS_REGION": "eu-north-1",
        "ASR_AWS_S3_BUCKET": "demo-bucket",
    }
    gui_main._run_aws_sts_preflight(env_merged)  # noqa: SLF001
    gui_main._run_aws_sts_preflight(env_merged)  # noqa: SLF001

    assert calls == ["boto3", "boto3"]
