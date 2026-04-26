from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from asr_gateway.secret_state import (
    azure_secret_status,
    google_secret_status,
    huggingface_secret_status,
    normalize_ref_name,
    secret_ref_path,
    validate_secret_file,
)


def test_normalize_ref_name_and_secret_ref_path(tmp_path: Path) -> None:
    refs_root = tmp_path / "refs"
    refs_root.mkdir()

    normalized = normalize_ref_name(
        "google_service_account.yaml",
        clean_name=lambda value, _what: value,
    )
    path = secret_ref_path(
        "google_service_account.yaml",
        secrets_refs_root=refs_root,
        clean_name=lambda value, _what: value,
    )

    assert normalized == "google_service_account"
    assert path == refs_root / "google_service_account.yaml"


def test_google_secret_status_reads_service_account_json(tmp_path: Path) -> None:
    credential_file = tmp_path / "service-account.json"
    credential_file.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "demo-project",
                "client_email": "demo-account@demo-project.iam.gserviceaccount.com",
                "private_key": "mock-private-key-material",
            }
        ),
        encoding="utf-8",
    )

    status = google_secret_status(
        "unused",
        resolved_file_path=str(credential_file),
        resolved_source="path",
    )

    assert status["runtime_ready"] is True
    assert status["status"] == "ready"
    assert status["project_id"] == "demo-project"
    assert status["client_email_masked"].endswith("@demo-project.iam.gserviceaccount.com")
    assert status["credential_type"] == "service_account"


def test_google_secret_status_detects_invalid_json(tmp_path: Path) -> None:
    credential_file = tmp_path / "service-account.json"
    credential_file.write_text("{not-json", encoding="utf-8")

    status = google_secret_status(
        "unused",
        resolved_file_path=str(credential_file),
        resolved_source="path",
    )

    assert status["runtime_ready"] is False
    assert status["status"] == "invalid_json"


def test_google_secret_status_detects_incomplete_service_account_json(tmp_path: Path) -> None:
    credential_file = tmp_path / "service-account.json"
    credential_file.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "demo-project",
            }
        ),
        encoding="utf-8",
    )

    status = google_secret_status(
        "unused",
        resolved_file_path=str(credential_file),
        resolved_source="path",
    )

    assert status["runtime_ready"] is False
    assert status["status"] == "invalid_service_account_json"


def test_azure_secret_status_reports_runtime_ready(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text("AZURE_SPEECH_KEY=test\nAZURE_SPEECH_REGION=eastus\n", encoding="utf-8")

    values = {
        "AZURE_SPEECH_KEY": ("test", "local_env_file"),
        "AZURE_SPEECH_REGION": ("eastus", "local_env_file"),
        "ASR_AZURE_ENDPOINT": ("https://example.invalid", "local_env_file"),
    }

    status = azure_secret_status(
        "secrets/refs/azure.yaml",
        resolve_env_value=lambda key, _source: values.get(key, ("", "")),
        local_env_file_path=lambda _source: env_file,
    )

    assert status["runtime_ready"] is True
    assert status["status"] == "ready"
    assert status["speech_key_source"] == "local_env_file"
    assert status["region"] == "eastus"
    assert status["endpoint_mode"] == "url"


def test_azure_secret_status_allows_endpoint_url_without_region(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text(
        "AZURE_SPEECH_KEY=test\nASR_AZURE_ENDPOINT=https://example.invalid\n",
        encoding="utf-8",
    )

    values = {
        "AZURE_SPEECH_KEY": ("test", "local_env_file"),
        "AZURE_SPEECH_REGION": ("", ""),
        "ASR_AZURE_ENDPOINT": ("https://example.invalid", "local_env_file"),
    }

    status = azure_secret_status(
        "secrets/refs/azure.yaml",
        resolve_env_value=lambda key, _source: values.get(key, ("", "")),
        local_env_file_path=lambda _source: env_file,
    )

    assert status["runtime_ready"] is True
    assert status["status"] == "ready"
    assert status["endpoint_mode"] == "url"
    assert status["region_required"] is False
    assert status["target_ready"] is True


def test_azure_secret_status_reports_missing_region(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text("AZURE_SPEECH_KEY=test\n", encoding="utf-8")

    values = {
        "AZURE_SPEECH_KEY": ("test", "local_env_file"),
        "AZURE_SPEECH_REGION": ("", ""),
        "ASR_AZURE_ENDPOINT": ("", ""),
    }

    status = azure_secret_status(
        "secrets/refs/azure.yaml",
        resolve_env_value=lambda key, _source: values.get(key, ("", "")),
        local_env_file_path=lambda _source: env_file,
    )

    assert status["runtime_ready"] is False
    assert status["status"] == "missing_region"


def test_huggingface_secret_status_marks_local_token_optional(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text("", encoding="utf-8")

    status = huggingface_secret_status(
        "secrets/refs/huggingface_local_token.yaml",
        provider="huggingface_local",
        token_required=False,
        resolve_env_value=lambda _key, _source: ("", ""),
        local_env_file_path=lambda _source: env_file,
    )

    assert status["runtime_ready"] is True
    assert status["token_present"] is False
    assert status["status"] == "optional_missing"


def test_huggingface_secret_status_requires_token_for_api(tmp_path: Path) -> None:
    env_file = tmp_path / "runtime.env"
    env_file.write_text("HF_TOKEN=hf_demo\n", encoding="utf-8")

    status = huggingface_secret_status(
        "secrets/refs/huggingface_api_token.yaml",
        provider="huggingface_api",
        token_required=True,
        resolve_env_value=lambda _key, _source: ("hf_demo", "local_env_file"),
        local_env_file_path=lambda _source: env_file,
    )

    assert status["runtime_ready"] is True
    assert status["token_present"] is True
    assert status["token_source"] == "local_env_file"
    assert status["status"] == "ready"


def test_validate_secret_file_builds_google_auth_detail(tmp_path: Path) -> None:
    refs_root = tmp_path / "secrets" / "refs"
    refs_root.mkdir(parents=True)
    ref_file = refs_root / "google_service_account.yaml"
    ref_file.write_text("placeholder", encoding="utf-8")
    credential_file = tmp_path / "secrets" / "google" / "service-account.json"
    credential_file.parent.mkdir(parents=True)
    credential_file.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "demo-project",
                "client_email": "demo-account@demo-project.iam.gserviceaccount.com",
                "private_key": "secret",
            }
        ),
        encoding="utf-8",
    )

    ref = SimpleNamespace(
        ref_id="google_service_account",
        provider="google",
        kind="file",
        path="secrets/google/service-account.json",
        env_fallback="",
        required=[],
        optional=[],
        masked=True,
        source_path=str(ref_file),
    )

    detail = validate_secret_file(
        ref_file,
        load_secret_ref=lambda _path: ref,
        resolve_secret_ref=lambda _ref: {"file_path": str(credential_file)},
        resolve_env_value=lambda _key, _source: ("", ""),
        aws_backend_factory=lambda: None,
        azure_status_factory=lambda _source: {},
        google_status_factory=lambda source, file_path, resolved_source: google_secret_status(
            source,
            resolved_file_path=file_path,
            resolved_source=resolved_source,
        ),
        huggingface_status_factory=lambda _source, _provider, _required: {},
    )

    assert detail["valid"] is True
    assert detail["resolved_file_path"] == str(credential_file)
    assert detail["auth"]["runtime_ready"] is True


def test_validate_secret_file_marks_invalid_google_auth_payload(tmp_path: Path) -> None:
    refs_root = tmp_path / "secrets" / "refs"
    refs_root.mkdir(parents=True)
    ref_file = refs_root / "google_service_account.yaml"
    ref_file.write_text("placeholder", encoding="utf-8")
    credential_file = tmp_path / "secrets" / "google" / "service-account.json"
    credential_file.parent.mkdir(parents=True)
    credential_file.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "demo-project",
            }
        ),
        encoding="utf-8",
    )

    ref = SimpleNamespace(
        ref_id="google_service_account",
        provider="google",
        kind="file",
        path="secrets/google/service-account.json",
        env_fallback="",
        required=[],
        optional=[],
        masked=True,
        source_path=str(ref_file),
    )

    detail = validate_secret_file(
        ref_file,
        load_secret_ref=lambda _path: ref,
        resolve_secret_ref=lambda _ref: {"file_path": str(credential_file)},
        resolve_env_value=lambda _key, _source: ("", ""),
        aws_backend_factory=lambda: None,
        azure_status_factory=lambda _source: {},
        google_status_factory=lambda source, file_path, resolved_source: google_secret_status(
            source,
            resolved_file_path=file_path,
            resolved_source=resolved_source,
        ),
        huggingface_status_factory=lambda _source, _provider, _required: {},
    )

    assert detail["valid"] is False
    assert detail["auth"]["runtime_ready"] is False
    assert detail["auth"]["status"] == "invalid_service_account_json"
    assert any("complete service-account JSON" in issue for issue in detail["issues"])


def test_validate_secret_file_includes_aws_auth_issues(tmp_path: Path) -> None:
    ref_file = tmp_path / "aws.yaml"
    ref_file.write_text("placeholder", encoding="utf-8")
    ref = SimpleNamespace(
        ref_id="aws_profile",
        provider="aws",
        kind="env",
        path="",
        env_fallback="",
        required=["AWS_PROFILE"],
        optional=["AWS_REGION"],
        masked=True,
        source_path=str(ref_file),
    )

    class _FakeAwsBackend:
        def auth_status(self):
            return {
                "profile": "ros2ws",
                "uses_sso": True,
                "runtime_ready": False,
                "status": "sso_login_required",
                "login_recommended": True,
            }

        def auth_validation_errors(self):
            return ["aws cli profile missing cached token"]

    detail = validate_secret_file(
        ref_file,
        load_secret_ref=lambda _path: ref,
        resolve_secret_ref=lambda _ref: {},
        resolve_env_value=lambda key, _source: (
            ("ros2ws", "process_env") if key == "AWS_PROFILE" else ("", "")
        ),
        aws_backend_factory=_FakeAwsBackend,
        azure_status_factory=lambda _source: {},
        google_status_factory=lambda _source, _file, _resolved_source: {},
        huggingface_status_factory=lambda _source, _provider, _required: {},
    )

    assert detail["valid"] is False
    assert detail["auth"]["login_supported"] is True
    assert detail["auth"]["login_command"] == "aws sso login --profile ros2ws"
    assert "aws cli profile missing cached token" in detail["issues"]


def test_validate_secret_file_builds_huggingface_auth_detail(tmp_path: Path) -> None:
    ref_file = tmp_path / "huggingface_api_token.yaml"
    ref_file.write_text("placeholder", encoding="utf-8")
    ref = SimpleNamespace(
        ref_id="huggingface_api_token",
        provider="huggingface_api",
        kind="env",
        path="",
        env_fallback="",
        required=["HF_TOKEN"],
        optional=[],
        masked=True,
        source_path=str(ref_file),
    )

    detail = validate_secret_file(
        ref_file,
        load_secret_ref=lambda _path: ref,
        resolve_secret_ref=lambda _ref: {},
        resolve_env_value=lambda key, _source: (
            ("hf_demo", "local_env_file") if key == "HF_TOKEN" else ("", "")
        ),
        aws_backend_factory=lambda: None,
        azure_status_factory=lambda _source: {},
        google_status_factory=lambda _source, _file, _resolved_source: {},
        huggingface_status_factory=lambda source, provider, required: huggingface_secret_status(
            source,
            provider=provider,
            token_required=required,
            resolve_env_value=lambda key, _source: (
                ("hf_demo", "local_env_file") if key == "HF_TOKEN" else ("", "")
            ),
            local_env_file_path=lambda _source: tmp_path / "runtime.env",
        ),
    )

    assert detail["valid"] is True
    assert detail["auth"]["runtime_ready"] is True
    assert detail["auth"]["status"] == "ready"
