"""AWS auth profile storage and runtime preparation helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from web_gui.app.paths import AWS_AUTH_PROFILES_DIR, RUNTIME_AWS_DIR

_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")
_KV_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$")

KNOWN_AWS_AUTH_KEYS = [
    "AWS_AUTH_TYPE",
    "AWS_PROFILE",
    "AWS_REGION",
    "AWS_S3_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_SSO_START_URL",
    "AWS_SSO_REGION",
    "AWS_SSO_ACCOUNT_ID",
    "AWS_SSO_ROLE_NAME",
    "AWS_SSO_SESSION_NAME",
]


def _safe_name(name: str) -> str:
    safe = _NAME_RE.sub("-", name.strip())
    safe = safe.strip("-._")
    return safe or "aws-auth"


def auth_profile_path(name: str) -> Path:
    """Return auth profile path by logical name."""
    return AWS_AUTH_PROFILES_DIR / f"{_safe_name(name)}.txt"


def list_auth_profiles() -> list[str]:
    """List available auth profile names."""
    if not AWS_AUTH_PROFILES_DIR.exists():
        return []
    names = [item.stem for item in AWS_AUTH_PROFILES_DIR.glob("*.txt")]
    return sorted(set(names))


def discover_sso_constants() -> tuple[list[str], list[str]]:
    """Collect distinct SSO start URLs and SSO regions from saved auth profiles."""
    start_urls: set[str] = set()
    regions: set[str] = set()
    for name in list_auth_profiles():
        try:
            _, values = load_auth_profile(name)
        except (FileNotFoundError, ValueError):
            continue
        start_url = str(values.get("AWS_SSO_START_URL", "")).strip()
        region = str(values.get("AWS_SSO_REGION", "")).strip()
        if start_url:
            start_urls.add(start_url)
        if region:
            regions.add(region)
    return sorted(start_urls), sorted(regions)


def parse_env_like_text(raw: str) -> dict[str, str]:
    """Parse KEY=VALUE lines from text profile."""
    values: dict[str, str] = {}
    for raw_line in str(raw or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _KV_RE.match(line)
        if match is None:
            raise ValueError(f"Invalid auth profile line: '{raw_line}'")
        key = match.group(1).strip()
        value = match.group(2).strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        values[key] = value
    return values


def dump_env_like_text(values: dict[str, str]) -> str:
    """Render dict into deterministic KEY=VALUE text profile."""
    normalized = {str(k).strip().upper(): str(v).strip() for k, v in values.items()}
    rows: list[str] = []
    emitted: set[str] = set()
    for key in KNOWN_AWS_AUTH_KEYS:
        value = normalized.get(key, "")
        if not value:
            continue
        rows.append(f"{key}={value}")
        emitted.add(key)
    for key in sorted(normalized.keys()):
        if key in emitted:
            continue
        value = normalized[key]
        if value:
            rows.append(f"{key}={value}")
    return "\n".join(rows) + ("\n" if rows else "")


def save_auth_profile(
    name: str,
    *,
    content: str = "",
    values: dict[str, str] | None = None,
) -> Path:
    """Persist AWS auth profile text file."""
    payload_values = dict(values or {})
    if content.strip():
        payload_values = parse_env_like_text(content)
    if not payload_values:
        raise ValueError("Auth profile is empty")
    path = auth_profile_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_env_like_text(payload_values), encoding="utf-8")
    return path


def load_auth_profile(name: str) -> tuple[str, dict[str, str]]:
    """Load auth profile and return raw content + parsed values."""
    path = auth_profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"AWS auth profile not found: {name}")
    content = path.read_text(encoding="utf-8")
    return content, parse_env_like_text(content)


@dataclass(slots=True)
class AwsAuthContext:
    """Resolved AWS auth context for one run."""

    name: str
    content: str
    values: dict[str, str]
    runtime_secrets: dict[str, str]
    env_extra: dict[str, str]
    profile_name: str


def _auth_type(values: dict[str, str]) -> str:
    explicit = str(values.get("AWS_AUTH_TYPE", "")).strip().lower()
    if explicit in {"sso", "access_keys"}:
        return explicit
    if values.get("AWS_SSO_START_URL") and values.get("AWS_SSO_REGION"):
        return "sso"
    return "access_keys"


def _write_runtime_aws_config(name: str, values: dict[str, str]) -> dict[str, str]:
    """Create local AWS config/credentials files for GUI job environment."""
    profile_name = str(values.get("AWS_PROFILE") or "default").strip() or "default"
    region = str(values.get("AWS_REGION") or "us-east-1").strip() or "us-east-1"
    sso_start_url = str(values.get("AWS_SSO_START_URL", "")).strip()
    sso_region = str(values.get("AWS_SSO_REGION", "")).strip()
    account_id = str(values.get("AWS_SSO_ACCOUNT_ID", "")).strip()
    role_name = str(values.get("AWS_SSO_ROLE_NAME", "")).strip()
    session_name = str(values.get("AWS_SSO_SESSION_NAME", "")).strip() or f"{_safe_name(name)}-sso"
    if not sso_start_url or not sso_region:
        raise ValueError(
            "SSO auth profile must include AWS_SSO_START_URL and AWS_SSO_REGION"
        )

    target_dir = RUNTIME_AWS_DIR / _safe_name(name)
    target_dir.mkdir(parents=True, exist_ok=True)
    config_path = target_dir / "config"
    credentials_path = target_dir / "credentials"
    if not credentials_path.exists():
        credentials_path.write_text("", encoding="utf-8")

    lines = [
        f"[sso-session {session_name}]",
        f"sso_start_url = {sso_start_url}",
        f"sso_region = {sso_region}",
        "sso_registration_scopes = sso:account:access",
        "",
        f"[profile {profile_name}]",
        f"sso_session = {session_name}",
    ]
    if account_id:
        lines.append(f"sso_account_id = {account_id}")
    if role_name:
        lines.append(f"sso_role_name = {role_name}")
    lines.extend(
        [
            f"region = {region}",
            "output = json",
            "",
            "[default]",
            f"sso_session = {session_name}",
        ]
    )
    if account_id:
        lines.append(f"sso_account_id = {account_id}")
    if role_name:
        lines.append(f"sso_role_name = {role_name}")
    lines.extend([f"region = {region}", "output = json", ""])
    config_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "AWS_CONFIG_FILE": str(config_path),
        "AWS_SHARED_CREDENTIALS_FILE": str(credentials_path),
        "AWS_PROFILE": profile_name,
        "AWS_REGION": region,
    }


def resolve_auth_context(name: str, *, for_login: bool = False) -> AwsAuthContext:
    """Resolve auth profile into runtime secrets + env vars for jobs."""
    raw_content, raw_values = load_auth_profile(name)
    values = {str(k).strip().upper(): str(v).strip() for k, v in raw_values.items()}
    auth_type = _auth_type(values)

    profile_name = str(values.get("AWS_PROFILE") or "default").strip() or "default"
    region = str(values.get("AWS_REGION") or "us-east-1").strip() or "us-east-1"
    runtime_secrets: dict[str, str] = {
        "aws_profile": profile_name,
        "aws_region": region,
    }
    if values.get("AWS_S3_BUCKET"):
        runtime_secrets["aws_s3_bucket"] = values["AWS_S3_BUCKET"]

    env_extra: dict[str, str] = {
        "AWS_PROFILE": profile_name,
        "AWS_REGION": region,
    }
    if auth_type == "sso":
        sso_env = _write_runtime_aws_config(name, values)
        has_account_and_role = bool(
            values.get("AWS_SSO_ACCOUNT_ID") and values.get("AWS_SSO_ROLE_NAME")
        )
        # Runtime jobs should not override AWS config with a session-only profile because
        # credentials resolution for SDK calls requires account+role bindings.
        if for_login or has_account_and_role:
            env_extra.update(sso_env)
    else:
        key_id = values.get("AWS_ACCESS_KEY_ID", "")
        secret_key = values.get("AWS_SECRET_ACCESS_KEY", "")
        if key_id:
            env_extra["AWS_ACCESS_KEY_ID"] = key_id
            runtime_secrets["aws_access_key_id"] = key_id
        if secret_key:
            env_extra["AWS_SECRET_ACCESS_KEY"] = secret_key
            runtime_secrets["aws_secret_access_key"] = secret_key
        if values.get("AWS_SESSION_TOKEN"):
            env_extra["AWS_SESSION_TOKEN"] = values["AWS_SESSION_TOKEN"]
            runtime_secrets["aws_session_token"] = values["AWS_SESSION_TOKEN"]

    return AwsAuthContext(
        name=name,
        content=raw_content,
        values=values,
        runtime_secrets=runtime_secrets,
        env_extra=env_extra,
        profile_name=profile_name,
    )
