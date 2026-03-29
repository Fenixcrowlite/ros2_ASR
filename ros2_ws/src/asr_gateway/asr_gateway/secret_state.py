"""Secret reference validation and provider auth state helpers."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from asr_backend_aws.backend import AwsAsrBackend


def normalize_ref_name(
    ref_name: str,
    *,
    clean_name: Callable[[str, str], str],
) -> str:
    name = clean_name(ref_name, "ref_name")
    return name[:-5] if name.endswith(".yaml") else name


def secret_ref_path(
    ref_name: str,
    *,
    secrets_refs_root: Path,
    clean_name: Callable[[str, str], str],
) -> Path:
    return secrets_refs_root / f"{normalize_ref_name(ref_name, clean_name=clean_name)}.yaml"


def aws_backend_from_current_env(
    *,
    secret_ref_source: str,
    resolve_env_value: Callable[[str, str], tuple[str, str]],
    backend_cls: type[AwsAsrBackend] = AwsAsrBackend,
) -> AwsAsrBackend:
    return backend_cls(
        config={
            "profile": resolve_env_value("AWS_PROFILE", secret_ref_source)[0],
            "region": resolve_env_value("AWS_REGION", secret_ref_source)[0],
            "access_key_id": resolve_env_value("AWS_ACCESS_KEY_ID", secret_ref_source)[0],
            "secret_access_key": resolve_env_value("AWS_SECRET_ACCESS_KEY", secret_ref_source)[0],
            "session_token": resolve_env_value("AWS_SESSION_TOKEN", secret_ref_source)[0],
            "config_file": resolve_env_value("AWS_CONFIG_FILE", secret_ref_source)[0],
            "shared_credentials_file": resolve_env_value(
                "AWS_SHARED_CREDENTIALS_FILE",
                secret_ref_source,
            )[0],
        }
    )


def azure_secret_status(
    ref_source_path: str,
    *,
    resolve_env_value: Callable[[str, str], tuple[str, str]],
    local_env_file_path: Callable[[str], Path],
) -> dict[str, Any]:
    key_value, key_source = resolve_env_value("AZURE_SPEECH_KEY", ref_source_path)
    region_value, region_source = resolve_env_value("AZURE_SPEECH_REGION", ref_source_path)
    endpoint_value, endpoint_source = resolve_env_value("ASR_AZURE_ENDPOINT", ref_source_path)
    local_env_path = local_env_file_path(ref_source_path)
    endpoint_text = str(endpoint_value or "").strip()
    endpoint_mode = "none"
    if endpoint_text:
        endpoint_mode = (
            "url"
            if endpoint_text.startswith(("https://", "http://", "wss://"))
            else "endpoint_id"
        )
    return {
        "runtime_ready": bool(key_value and region_value),
        "local_env_file": str(local_env_path),
        "local_env_file_exists": local_env_path.exists(),
        "speech_key_present": bool(key_value),
        "speech_key_source": key_source or "missing",
        "speech_key_masked": "***" if key_value else "",
        "region": region_value,
        "region_source": region_source or "missing",
        "endpoint": endpoint_value,
        "endpoint_source": endpoint_source or "missing",
        "endpoint_mode": endpoint_mode,
        "message": (
            "Azure Speech credentials are ready for provider validation and runtime use."
            if key_value and region_value
            else "Azure needs AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
        ),
    }


def mask_email(value: str) -> str:
    text = str(value or "").strip()
    if not text or "@" not in text:
        return text
    name, domain = text.split("@", 1)
    if len(name) <= 2:
        masked_name = "*" * len(name)
    else:
        masked_name = f"{name[:2]}***{name[-1:]}"
    return f"{masked_name}@{domain}"


def google_secret_status(
    ref_source_path: str,
    *,
    resolved_file_path: str = "",
    resolved_source: str = "",
) -> dict[str, Any]:
    del ref_source_path
    file_path = str(resolved_file_path or "").strip()
    source = str(resolved_source or "").strip() or "missing"
    auth: dict[str, Any] = {
        "runtime_ready": False,
        "file_path": file_path,
        "file_source": source,
        "file_exists": bool(file_path and Path(file_path).exists()),
        "service_account_valid": False,
        "project_id": "",
        "client_email_masked": "",
        "credential_type": "",
        "message": "",
    }
    if not file_path:
        auth["message"] = "Google needs a service-account JSON file."
        return auth
    path = Path(file_path)
    if not path.exists():
        auth["message"] = f"Referenced Google credentials file does not exist: {file_path}"
        return auth

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        auth["message"] = f"Google credentials JSON is unreadable: {exc}"
        return auth

    if not isinstance(payload, dict):
        auth["message"] = "Google credentials file must be a JSON object."
        return auth

    auth["credential_type"] = str(payload.get("type", "") or "")
    auth["project_id"] = str(payload.get("project_id", "") or "")
    auth["client_email_masked"] = mask_email(str(payload.get("client_email", "") or ""))
    auth["service_account_valid"] = (
        auth["credential_type"] == "service_account"
        and bool(payload.get("project_id"))
        and bool(payload.get("client_email"))
        and bool(payload.get("private_key"))
    )
    auth["runtime_ready"] = bool(auth["service_account_valid"])
    auth["message"] = (
        "Google service-account JSON is ready for provider validation and runtime use."
        if auth["runtime_ready"]
        else (
            "Google credentials file is present but does not look like a complete "
            "service-account JSON."
        )
    )
    return auth


def validate_secret_file(
    path: Path,
    *,
    load_secret_ref: Callable[[str], Any],
    resolve_secret_ref: Callable[[Any], dict[str, str]],
    resolve_env_value: Callable[[str, str], tuple[str, str]],
    aws_backend_factory: Callable[[], Any],
    azure_status_factory: Callable[[str], dict[str, Any]],
    google_status_factory: Callable[[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    issues: list[str] = []
    detail: dict[str, Any] = {"valid": True, "issues": issues, "env": {}}

    if not path.exists():
        issues.append("secret ref file is missing")
        detail["valid"] = False
        return detail

    try:
        ref = load_secret_ref(str(path))
    except Exception as exc:
        issues.append(str(exc))
        detail["valid"] = False
        return detail

    detail.update(
        {
            "ref_id": ref.ref_id,
            "provider": ref.provider,
            "kind": ref.kind,
            "path": ref.path,
            "env_fallback": ref.env_fallback,
            "required": ref.required,
            "optional": ref.optional,
            "masked": ref.masked,
        }
    )

    if ref.kind not in {"none", "env", "file"}:
        issues.append(f"unsupported kind: {ref.kind}")

    if ref.kind == "file":
        file_path = ref.path
        source = "path"
        try:
            resolved = resolve_secret_ref(ref)
            file_path = str(resolved.get("file_path", ""))
            if ref.env_fallback:
                _, env_source = resolve_env_value(ref.env_fallback, ref.source_path)
                if env_source == "process_env":
                    source = "env_fallback"
                elif env_source == "local_env_file":
                    source = "env_fallback_local_env_file"
        except Exception as exc:
            if str(exc):
                issues.append(str(exc))
        detail["resolved_file_path"] = file_path
        detail["resolved_file_path_source"] = source
        if file_path and not Path(file_path).exists():
            issues.append(f"resolved credential file not found: {file_path}")
        if not file_path:
            issues.append("credential file path is not set")

    backend = None
    if ref.provider == "aws" and ref.kind == "env":
        backend = aws_backend_factory()
        auth = backend.auth_status()
        auth["login_supported"] = bool(auth.get("uses_sso") and auth.get("profile"))
        auth["login_recommended"] = bool(auth.get("login_recommended")) or str(
            auth.get("status", "")
        ) in {
            "role_credentials_valid_sso_expired",
            "sso_session_expired",
            "sso_login_required",
        }
        if auth.get("login_supported"):
            auth["login_command"] = f"aws sso login --profile {auth.get('profile', '')}"
        detail["auth"] = auth

    for name in ref.required:
        value, source = resolve_env_value(name, ref.source_path)
        present = bool(value)
        detail["env"][name] = {"present": present, "required": True, "source": source or "missing"}
        if ref.provider == "aws" and ref.kind == "env":
            continue
        if not present:
            issues.append(f"required env missing: {name}")

    for name in ref.optional:
        value, source = resolve_env_value(name, ref.source_path)
        present = bool(value)
        detail["env"][name] = {
            "present": present,
            "required": False,
            "source": source or "missing",
        }

    if ref.provider == "aws" and ref.kind == "env" and backend is not None:
        issues.extend(
            issue
            for issue in backend.auth_validation_errors()
            if issue and issue not in issues
        )
    if ref.provider == "azure" and ref.kind == "env":
        detail["auth"] = azure_status_factory(ref.source_path)
    if ref.provider == "google" and ref.kind == "file":
        detail["auth"] = google_status_factory(
            ref.source_path,
            str(detail.get("resolved_file_path", "") or ""),
            str(detail.get("resolved_file_path_source", "") or ""),
        )

    detail["valid"] = not issues
    return detail
