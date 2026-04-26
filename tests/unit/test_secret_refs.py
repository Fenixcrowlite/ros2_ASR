from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from asr_config.secrets import (
    load_secret_ref,
    mask_secret_values,
    resolve_env_value,
    resolve_secret_ref,
    write_local_env_values,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_env_secret_ref_resolution_requires_required_envs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ref_path = tmp_path / "azure.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/azure",
            "provider": "azure",
            "kind": "env",
            "required": ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
            "optional": ["AZURE_ENDPOINT"],
        },
    )
    ref = load_secret_ref(str(ref_path))

    monkeypatch.setenv("AZURE_SPEECH_KEY", "super-secret-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setenv("AZURE_ENDPOINT", "https://example.invalid")

    resolved = resolve_secret_ref(ref)

    assert resolved["AZURE_SPEECH_KEY"] == "super-secret-key"
    assert resolved["AZURE_SPEECH_REGION"] == "eastus"
    assert resolved["AZURE_ENDPOINT"] == "https://example.invalid"


def test_file_secret_ref_uses_env_fallback_and_checks_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    secret_file = tmp_path / "service-account.json"
    secret_file.write_text("{}", encoding="utf-8")
    ref_path = tmp_path / "google.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/google",
            "provider": "google",
            "kind": "file",
            "path": "",
            "env_fallback": "GOOGLE_APPLICATION_CREDENTIALS",
        },
    )
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(secret_file))

    ref = load_secret_ref(str(ref_path))
    resolved = resolve_secret_ref(ref)

    assert resolved["file_path"] == str(secret_file)


def test_file_secret_ref_resolves_relative_path_from_project_layout(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    refs_dir = project_root / "secrets" / "refs"
    google_dir = project_root / "secrets" / "google"
    refs_dir.mkdir(parents=True)
    google_dir.mkdir(parents=True)
    secret_file = google_dir / "service-account.json"
    secret_file.write_text("{}", encoding="utf-8")
    ref_path = refs_dir / "google.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/google",
            "provider": "google",
            "kind": "file",
            "path": "secrets/google/service-account.json",
        },
    )

    ref = load_secret_ref(str(ref_path))
    resolved = resolve_secret_ref(ref)

    assert resolved["file_path"] == str(secret_file)


def test_secret_ref_raises_for_missing_required_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref_path = tmp_path / "aws.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/aws",
            "provider": "aws",
            "kind": "env",
            "required": ["AWS_PROFILE"],
        },
    )

    monkeypatch.delenv("AWS_PROFILE", raising=False)
    ref = load_secret_ref(str(ref_path))
    with pytest.raises(ValueError, match="AWS_PROFILE"):
        resolve_secret_ref(ref)


def test_env_secret_ref_can_use_local_env_injection_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    refs_dir = project_root / "secrets" / "refs"
    refs_dir.mkdir(parents=True)
    ref_path = refs_dir / "azure.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/azure",
            "provider": "azure",
            "kind": "env",
            "required": ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
            "optional": ["ASR_AZURE_ENDPOINT"],
        },
    )
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)
    monkeypatch.delenv("ASR_AZURE_ENDPOINT", raising=False)

    write_local_env_values(
        {
            "AZURE_SPEECH_KEY": "azure-secret",
            "AZURE_SPEECH_REGION": "eastus",
            "ASR_AZURE_ENDPOINT": "https://example.invalid",
        },
        source_path=str(ref_path),
    )

    ref = load_secret_ref(str(ref_path))
    resolved = resolve_secret_ref(ref)
    endpoint_value, endpoint_source = resolve_env_value("ASR_AZURE_ENDPOINT", str(ref_path))

    assert resolved["AZURE_SPEECH_KEY"] == "azure-secret"
    assert resolved["AZURE_SPEECH_REGION"] == "eastus"
    assert endpoint_value == "https://example.invalid"
    assert endpoint_source == "local_env_file"


def test_azure_env_secret_ref_allows_endpoint_url_without_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    refs_dir = project_root / "secrets" / "refs"
    refs_dir.mkdir(parents=True)
    ref_path = refs_dir / "azure.yaml"
    _write_yaml(
        ref_path,
        {
            "ref_id": "secrets/azure",
            "provider": "azure",
            "kind": "env",
            "required": ["AZURE_SPEECH_KEY"],
            "optional": ["AZURE_SPEECH_REGION", "ASR_AZURE_ENDPOINT"],
        },
    )
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)
    monkeypatch.delenv("ASR_AZURE_ENDPOINT", raising=False)

    write_local_env_values(
        {
            "AZURE_SPEECH_KEY": "azure-secret",
            "ASR_AZURE_ENDPOINT": "https://example.invalid",
        },
        source_path=str(ref_path),
    )

    ref = load_secret_ref(str(ref_path))
    resolved = resolve_secret_ref(ref)

    assert resolved["AZURE_SPEECH_KEY"] == "azure-secret"
    assert resolved["ASR_AZURE_ENDPOINT"] == "https://example.invalid"
    assert "AZURE_SPEECH_REGION" not in resolved


def test_mask_secret_values_never_returns_full_plaintext() -> None:
    masked = mask_secret_values(
        {
            "SHORT": "abc",
            "LONG": "supersecretvalue",
            "EMPTY": "",
        }
    )

    assert masked["SHORT"] == "***"
    assert masked["LONG"].startswith("su***")
    assert masked["LONG"] != "supersecretvalue"
    assert masked["EMPTY"] == ""


def test_write_local_env_values_rejects_invalid_env_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid env key"):
        write_local_env_values({"BAD-KEY": "value"}, source_path=str(tmp_path / "refs.yaml"))


def test_write_local_env_values_rejects_multiline_env_value(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="control characters"):
        write_local_env_values(
            {"HF_TOKEN": "hf_demo\nINJECTED=1"},
            source_path=str(tmp_path / "refs.yaml"),
        )
