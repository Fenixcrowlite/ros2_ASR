#!/usr/bin/env python3
"""Sanitized credential discovery for thesis cloud provider checks."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILES = (
    ".env",
    ".env.local",
    "secrets/.env",
    "configs/.env",
    "secrets/local/runtime.env",
)

PROVIDER_CONFIGS = {
    "huggingface_api": "configs/providers/huggingface_api.yaml",
    "azure_cloud": "configs/providers/azure_cloud.yaml",
    "google_cloud": "configs/providers/google_cloud.yaml",
    "aws_cloud": "configs/providers/aws_cloud.yaml",
}

SUPPORTED_ENV_NAMES = (
    "HF_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "SPEECH_KEY",
    "SPEECH_REGION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GCP_PROJECT",
    "AWS_PROFILE",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_TRANSCRIBE_BUCKET",
    "AWS_S3_BUCKET",
    "ASR_AWS_S3_BUCKET",
)

PROVIDER_REQUIRED_SECRET_NAMES = {
    "huggingface_api": ["HF_TOKEN or HUGGINGFACEHUB_API_TOKEN"],
    "azure_cloud": [
        "AZURE_SPEECH_KEY or SPEECH_KEY",
        "AZURE_SPEECH_REGION or SPEECH_REGION",
    ],
    "google_cloud": [
        "GOOGLE_APPLICATION_CREDENTIALS or ADC",
        "GOOGLE_CLOUD_PROJECT or GCP_PROJECT",
    ],
    "aws_cloud": [
        "AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY",
        "AWS_REGION or AWS_DEFAULT_REGION",
        "AWS_TRANSCRIBE_BUCKET or AWS_S3_BUCKET or ASR_AWS_S3_BUCKET",
    ],
}


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value:
            values[key] = value
    return values


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _path_exists(raw_path: str) -> bool:
    if not raw_path:
        return False
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.exists()


def _resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _discover_sources() -> tuple[dict[str, str], dict[str, list[str]]]:
    values: dict[str, str] = {}
    sources: dict[str, list[str]] = {}

    for key in SUPPORTED_ENV_NAMES:
        value = os.getenv(key, "").strip()
        if value:
            values[key] = value
            sources.setdefault(key, []).append("process_env")

    for rel_path in ENV_FILES:
        env_path = PROJECT_ROOT / rel_path
        for key, value in _read_env_file(env_path).items():
            if key not in SUPPORTED_ENV_NAMES:
                continue
            if key not in values:
                values[key] = value
            sources.setdefault(key, []).append(rel_path)

    for ref_path in sorted((PROJECT_ROOT / "secrets" / "refs").glob("*.yaml")):
        ref = _load_yaml(ref_path)
        ref_keys = [*(ref.get("required", []) or []), *(ref.get("optional", []) or [])]
        for key in ref_keys:
            if str(key) in SUPPORTED_ENV_NAMES:
                sources.setdefault(str(key), []).append(str(ref_path.relative_to(PROJECT_ROOT)))
        env_fallback = str(ref.get("env_fallback", "") or "").strip()
        if env_fallback in SUPPORTED_ENV_NAMES:
            sources.setdefault(env_fallback, []).append(str(ref_path.relative_to(PROJECT_ROOT)))
        if str(ref.get("kind", "") or "") == "file":
            file_path = str(ref.get("path", "") or "").strip()
            if file_path and _path_exists(file_path):
                resolved_file = _resolve_path(file_path).resolve()
                values.setdefault("__GOOGLE_ADC_FILE__", str(resolved_file))
                sources.setdefault("__GOOGLE_ADC_FILE__", []).append(
                    str(ref_path.relative_to(PROJECT_ROOT))
                )
                if str(ref.get("provider", "") or "") == "google":
                    project_id = str(
                        _load_json_object(resolved_file).get("project_id", "") or ""
                    ).strip()
                    if project_id:
                        values.setdefault("__GOOGLE_PROJECT_ID_FROM_FILE__", project_id)
                        sources.setdefault("__GOOGLE_PROJECT_ID_FROM_FILE__", []).append(
                            str(ref_path.relative_to(PROJECT_ROOT))
                        )

    for provider_config in PROVIDER_CONFIGS.values():
        cfg_path = PROJECT_ROOT / provider_config
        cfg = _load_yaml(cfg_path)
        credentials_ref = str(cfg.get("credentials_ref", "") or "").strip()
        if credentials_ref:
            sources.setdefault("__PROVIDER_CONFIG__", []).append(provider_config)
        settings = cfg.get("settings", {})
        if isinstance(settings, dict):
            for value in settings.values():
                text = str(value or "").strip()
                if text.startswith("${") and text.endswith("}"):
                    key = text[2:-1]
                    if key in SUPPORTED_ENV_NAMES:
                        sources.setdefault(key, []).append(provider_config)

    return values, sources


def apply_discovered_environment() -> dict[str, str]:
    """Load supported env-file secrets into this process without overwriting env."""
    values, _ = _discover_sources()
    aws_bucket, _, _ = _discover_aws_bucket(values)
    if aws_bucket:
        values.setdefault("__AWS_DISCOVERED_BUCKET__", aws_bucket)
    aliases = {
        "HUGGINGFACEHUB_API_TOKEN": "HF_TOKEN",
        "SPEECH_KEY": "AZURE_SPEECH_KEY",
        "SPEECH_REGION": "AZURE_SPEECH_REGION",
        "GCP_PROJECT": "GOOGLE_CLOUD_PROJECT",
        "__GOOGLE_PROJECT_ID_FROM_FILE__": "GOOGLE_CLOUD_PROJECT",
        "AWS_DEFAULT_REGION": "AWS_REGION",
        "AWS_TRANSCRIBE_BUCKET": "AWS_S3_BUCKET",
        "__AWS_DISCOVERED_BUCKET__": "AWS_S3_BUCKET",
    }
    for key, value in values.items():
        if key in aliases:
            os.environ.setdefault(aliases[key], value)
            continue
        if key.startswith("__"):
            continue
        os.environ.setdefault(key, value)
    return {key: value for key, value in values.items() if not key.startswith("__")}


def _google_adc_available(values: dict[str, str]) -> tuple[bool, str]:
    credentials_path = values.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if credentials_path:
        return _path_exists(credentials_path), "GOOGLE_APPLICATION_CREDENTIALS"
    if values.get("__GOOGLE_ADC_FILE__"):
        return True, "secret_ref_file"
    try:
        import google.auth  # type: ignore[import-not-found]

        google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        return True, "application_default_credentials"
    except Exception:
        return False, ""


def _discover_aws_bucket(values: dict[str, str]) -> tuple[str, str, str]:
    explicit_bucket = (
        values.get("AWS_TRANSCRIBE_BUCKET")
        or values.get("AWS_S3_BUCKET")
        or values.get("ASR_AWS_S3_BUCKET")
    )
    if explicit_bucket:
        return explicit_bucket, "configured", ""

    has_auth = bool(
        values.get("AWS_PROFILE")
        or (values.get("AWS_ACCESS_KEY_ID") and values.get("AWS_SECRET_ACCESS_KEY"))
    )
    if not has_auth:
        return "", "", "AWS auth not available for S3 bucket discovery"

    try:
        import boto3  # type: ignore[import-not-found]

        region = values.get("AWS_REGION") or values.get("AWS_DEFAULT_REGION") or None
        kwargs: dict[str, str] = {}
        if values.get("AWS_PROFILE"):
            kwargs["profile_name"] = values["AWS_PROFILE"]
        if region:
            kwargs["region_name"] = region
        if values.get("AWS_ACCESS_KEY_ID") and values.get("AWS_SECRET_ACCESS_KEY"):
            kwargs["aws_access_key_id"] = values["AWS_ACCESS_KEY_ID"]
            kwargs["aws_secret_access_key"] = values["AWS_SECRET_ACCESS_KEY"]
            if values.get("AWS_SESSION_TOKEN"):
                kwargs["aws_session_token"] = values["AWS_SESSION_TOKEN"]

        session = boto3.Session(**kwargs)
        s3 = session.client("s3", region_name=region)
        buckets = [
            str(item.get("Name", "") or "")
            for item in s3.list_buckets().get("Buckets", [])
            if str(item.get("Name", "") or "")
        ]
        preferred_tokens = ("asr", "transcribe", "speech", "ros", "thesis", "benchmark")
        buckets = sorted(
            buckets,
            key=lambda name: (
                0 if any(token in name.lower() for token in preferred_tokens) else 1,
                name,
            ),
        )
        for bucket in buckets:
            try:
                s3.head_bucket(Bucket=bucket)
            except Exception:
                continue
            return bucket, "aws_list_buckets", ""
        return "", "aws_list_buckets", "no accessible S3 bucket found"
    except Exception as exc:  # noqa: BLE001 - report sanitized status only.
        detail = str(exc).strip() or exc.__class__.__name__
        return "", "aws_list_buckets", f"bucket discovery failed: {detail[:180]}"


def discover_credentials() -> dict[str, Any]:
    values, sources = _discover_sources()

    hf_token = values.get("HF_TOKEN") or values.get("HUGGINGFACEHUB_API_TOKEN")
    azure_key = values.get("AZURE_SPEECH_KEY") or values.get("SPEECH_KEY")
    azure_region = values.get("AZURE_SPEECH_REGION") or values.get("SPEECH_REGION")
    google_creds, google_creds_source = _google_adc_available(values)
    google_project = (
        values.get("GOOGLE_CLOUD_PROJECT")
        or values.get("GCP_PROJECT")
        or values.get("__GOOGLE_PROJECT_ID_FROM_FILE__")
    )
    aws_auth = bool(
        values.get("AWS_PROFILE")
        or (values.get("AWS_ACCESS_KEY_ID") and values.get("AWS_SECRET_ACCESS_KEY"))
    )
    aws_region = values.get("AWS_REGION") or values.get("AWS_DEFAULT_REGION")
    aws_bucket, aws_bucket_source, aws_bucket_error = _discover_aws_bucket(values)
    if aws_bucket:
        values.setdefault("__AWS_DISCOVERED_BUCKET__", aws_bucket)
        sources.setdefault("__AWS_DISCOVERED_BUCKET__", []).append(aws_bucket_source)

    provider_states = {
        "huggingface_api": {
            "requirements": {"token": "available" if hf_token else "missing"},
            "credential_detected": bool(hf_token),
            "config_complete": bool(hf_token),
        },
        "azure_cloud": {
            "requirements": {
                "speech_key": "available" if azure_key else "missing",
                "region": "available" if azure_region else "missing",
            },
            "credential_detected": bool(azure_key or azure_region),
            "config_complete": bool(azure_key and azure_region),
        },
        "google_cloud": {
            "requirements": {
                "credentials": "available" if google_creds else "missing",
                "project_id": "available" if google_project else "missing",
            },
            "credential_detected": bool(google_creds or google_project),
            "config_complete": bool(google_creds and google_project),
            "credential_mode": google_creds_source,
        },
        "aws_cloud": {
            "requirements": {
                "auth": "available" if aws_auth else "missing",
                "region": "available" if aws_region else "missing",
                "bucket": "available" if aws_bucket else "missing",
            },
            "credential_detected": bool(
                aws_auth
                or aws_region
                or aws_bucket
                or values.get("AWS_SESSION_TOKEN")
            ),
            "config_complete": bool(aws_auth and aws_region and aws_bucket),
            "bucket_mode": aws_bucket_source,
            "bucket_error": aws_bucket_error,
        },
    }

    providers: list[dict[str, Any]] = []
    for provider, state in provider_states.items():
        missing = [
            key for key, status in state["requirements"].items() if status != "available"
        ]
        if state["config_complete"]:
            status = "available"
            summary = ""
        elif state["credential_detected"]:
            status = "found_but_config_incomplete"
            summary = "missing " + ", ".join(missing)
        else:
            status = "missing"
            summary = "no supported credential source detected"
        detected_sources = sorted(
            {
                source
                for name, source_list in sources.items()
                for source in source_list
                if name in SUPPORTED_ENV_NAMES
                or name
                in {
                    "__GOOGLE_ADC_FILE__",
                    "__GOOGLE_PROJECT_ID_FROM_FILE__",
                    "__AWS_DISCOVERED_BUCKET__",
                    "__PROVIDER_CONFIG__",
                }
            }
        )
        providers.append(
            {
                "provider": provider,
                "required_secret_names": PROVIDER_REQUIRED_SECRET_NAMES[provider],
                "secret_source_detected": detected_sources,
                "requirements": state["requirements"],
                "credential_detected": state["credential_detected"],
                "config_complete": state["config_complete"],
                "auth_probe_status": "not_run",
                "safe_error_summary": summary,
                **({"credential_mode": state["credential_mode"]} if "credential_mode" in state else {}),
                **({"bucket_mode": state["bucket_mode"]} if "bucket_mode" in state else {}),
            }
        )
        if provider == "aws_cloud" and state.get("bucket_error") and not state["config_complete"]:
            providers[-1]["safe_error_summary"] = str(state["bucket_error"])

    return {
        "created_at": datetime.now(UTC).isoformat(),
        "providers": providers,
    }


def write_credential_reports(
    *,
    output_json: Path = PROJECT_ROOT / "reports" / "thesis_test" / "credential_availability.json",
    output_md: Path = PROJECT_ROOT / "reports" / "thesis_test" / "credential_availability.md",
    smoke_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = discover_credentials()
    smoke_by_provider = {str(row.get("provider", "") or ""): row for row in smoke_rows or []}
    for provider in payload["providers"]:
        smoke = smoke_by_provider.get(provider["provider"])
        if smoke:
            auth_success = str(smoke.get("auth_probe_success", "")).lower() == "true"
            smoke_success = str(smoke.get("smoke_recognition_success", "")).lower() == "true"
            if auth_success and smoke_success:
                provider["auth_probe_status"] = "success"
                provider["credential_detected"] = True
                provider["config_complete"] = True
                provider["safe_error_summary"] = ""
                if provider["provider"] == "aws_cloud":
                    requirements = provider.setdefault("requirements", {})
                    if requirements.get("bucket") == "missing":
                        if provider.get("bucket_mode") == "aws_list_buckets":
                            requirements["bucket"] = "available"
                        else:
                            requirements["bucket"] = "not_required_for_this_mode"
                            provider["bucket_mode"] = "not_required_for_this_mode"
            elif str(smoke.get("error_type", "") or ""):
                provider["auth_probe_status"] = "failure"
                provider["safe_error_summary"] = str(
                    smoke.get("error_message_sanitized", "") or smoke.get("error_type", "")
                )
            else:
                provider["auth_probe_status"] = "not_run"

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Credential Availability",
        "",
        f"Created: `{payload['created_at']}`",
        "",
        "| Provider | Required Secrets | Sources Checked/Detected | Auth Probe | Status | Safe Error Summary |",
        "|---|---|---|---|---|---|",
    ]
    for provider in payload["providers"]:
        status = "available" if provider["config_complete"] else (
            "found_but_config_incomplete" if provider["credential_detected"] else "missing"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    provider["provider"],
                    ", ".join(provider["required_secret_names"]),
                    ", ".join(provider["secret_source_detected"]) or "none",
                    provider["auth_probe_status"],
                    status,
                    provider["safe_error_summary"],
                ]
            )
            + " |"
        )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    apply_discovered_environment()
    result = write_credential_reports()
    print(json.dumps({"providers": len(result["providers"]), "output": "reports/thesis_test"}, indent=2))
