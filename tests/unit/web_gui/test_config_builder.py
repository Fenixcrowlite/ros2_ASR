from __future__ import annotations

from pathlib import Path

import pytest

from web_gui.app.config_builder import ConfigBuildError, build_runtime_config, deep_merge


def test_deep_merge_nested() -> None:
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    override = {"nested": {"y": 9, "z": 3}, "b": 2}
    merged = deep_merge(base, override)
    assert merged == {"a": 1, "b": 2, "nested": {"x": 1, "y": 9, "z": 3}}


def test_build_runtime_config_keeps_sensitive_values_in_env(tmp_path: Path) -> None:
    creds = tmp_path / "gcp.json"
    creds.write_text("{}", encoding="utf-8")
    path, merged, env = build_runtime_config(
        base_config_path="configs/default.yaml",
        runtime_overrides={"asr": {"backend": "google"}},
        secrets={
            "google_credentials_json": str(creds),
            "aws_profile": "ros2ws",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "SECRET",
            "azure_speech_key": "AZKEY",
            "azure_region": "westeurope",
            "aws_s3_bucket": "demo-bucket",
        },
        profile_name="unit_web_gui",
    )

    assert path.exists()
    assert merged["backends"]["aws"]["profile"] == "ros2ws"
    assert merged["backends"]["aws"]["s3_bucket"] == "demo-bucket"
    assert "credentials_json" not in merged["backends"]["google"]
    assert "access_key_id" not in merged["backends"]["aws"]
    assert "secret_access_key" not in merged["backends"]["aws"]
    assert "speech_key" not in merged["backends"]["azure"]
    assert env["GOOGLE_APPLICATION_CREDENTIALS"] == str(creds)
    assert env["AWS_PROFILE"] == "ros2ws"
    assert env["AWS_ACCESS_KEY_ID"] == "AKIA123"
    assert env["AWS_SECRET_ACCESS_KEY"] == "SECRET"
    assert env["AZURE_SPEECH_KEY"] == "AZKEY"
    assert env["ASR_AWS_S3_BUCKET"] == "demo-bucket"


def test_build_runtime_config_rejects_incomplete_aws_access_key_pair() -> None:
    with pytest.raises(
        ConfigBuildError,
        match="both aws_access_key_id and aws_secret_access_key",
    ):
        build_runtime_config(
            base_config_path="configs/default.yaml",
            runtime_overrides={},
            secrets={"aws_access_key_id": "AKIA123"},
            profile_name="unit_web_gui",
        )


def test_build_runtime_config_rejects_missing_google_credential_file() -> None:
    with pytest.raises(ConfigBuildError, match="Google credentials file not found"):
        build_runtime_config(
            base_config_path="configs/default.yaml",
            runtime_overrides={},
            secrets={"google_credentials_json": "/tmp/definitely_missing_gcp_creds.json"},
            profile_name="unit_web_gui",
        )
