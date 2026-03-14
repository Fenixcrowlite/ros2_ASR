"""FastAPI server for ROS2 ASR Web GUI."""

from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import subprocess
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from web_gui.app.aws_auth_store import (
    auth_profile_path,
    dump_env_like_text,
    list_auth_profiles,
    load_auth_profile,
    resolve_auth_context,
    save_auth_profile,
)
from web_gui.app.command_builder import (
    CommandSpec,
    build_benchmark_command,
    build_live_sample_command,
    build_ros_bringup_command,
)
from web_gui.app.config_builder import ConfigBuildError, build_runtime_config
from web_gui.app.filesystem import list_noisy_samples, list_results, list_uploads
from web_gui.app.job_manager import JobManager
from web_gui.app.noise_service import apply_noise_levels
from web_gui.app.options import get_options_payload, list_profiles
from web_gui.app.paths import (
    LOGS_DIR,
    NOISY_DIR,
    REPO_ROOT,
    RUNTIME_CONFIGS_DIR,
    UPLOADS_DIR,
    WEB_GUI_ROOT,
    ensure_directories,
    resolve_under_roots,
)
from web_gui.app.preflight import run_preflight_checks
from web_gui.app.profile_store import load_profile, save_profile
from web_gui.app.validators import (
    validate_benchmark_request,
    validate_live_request,
    validate_ros_bringup_request,
)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    ensure_directories()
    yield


app = FastAPI(title="ROS2 ASR Web GUI", version="1.0.0", lifespan=_lifespan)
app.mount("/static", StaticFiles(directory=str(WEB_GUI_ROOT / "static")), name="static")
UPLOAD_FILE_PARAM = File(...)

JOBS = JobManager()
ALLOWED_ARTIFACT_ROOTS = [
    REPO_ROOT / "results",
    REPO_ROOT / "web_gui",
    REPO_ROOT / "docs",
    REPO_ROOT / "configs",
    REPO_ROOT / "data",
    RUNTIME_CONFIGS_DIR,
    UPLOADS_DIR,
    NOISY_DIR,
    LOGS_DIR,
]
LOGGER = logging.getLogger(__name__)
_AWS_STS_PREFLIGHT_CACHE: dict[str, float] = {}


class RunRequest(BaseModel):
    """Common request envelope for jobs."""

    profile_name: str = ""
    base_config: str = "configs/default.yaml"
    runtime_overrides: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, str] = Field(default_factory=dict)
    aws_auth_profile: str = ""


class SaveProfileRequest(BaseModel):
    """Profile persistence request."""

    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


class NoiseRequest(BaseModel):
    """Noise augmentation request."""

    source_wav: str
    snr_levels: list[float] = Field(default_factory=lambda: [20.0, 10.0, 0.0])


class SaveAwsAuthProfileRequest(BaseModel):
    """AWS auth profile persistence request."""

    name: str
    content: str = ""
    values: dict[str, str] = Field(default_factory=dict)


class AwsSsoLoginRequest(BaseModel):
    """AWS SSO login job request."""

    auth_profile: str
    use_device_code: bool = True
    no_browser: bool = False


def _backend_cfg(merged_cfg: dict[str, Any], backend: str) -> dict[str, Any]:
    backends = merged_cfg.get("backends", {})
    if not isinstance(backends, dict):
        return {}
    item = backends.get(backend, {})
    return item if isinstance(item, dict) else {}


def _backend_from_target(raw: str) -> str:
    token = str(raw or "").strip().lower()
    if not token:
        return ""
    token = token.split("@", 1)[0]
    token = token.split(":", 1)[0]
    return token.strip()


def _requested_backends(payload: dict[str, Any], merged_cfg: dict[str, Any]) -> set[str]:
    selected: set[str] = set()
    has_explicit_targets = False

    for key in ("backends", "model_runs"):
        raw_value = payload.get(key, "")
        if isinstance(raw_value, list):
            tokens = [str(item) for item in raw_value]
        else:
            tokens = str(raw_value).split(",")
        for token in tokens:
            backend = _backend_from_target(token)
            if backend:
                selected.add(backend)
                has_explicit_targets = True

    if has_explicit_targets:
        return selected

    asr_cfg = merged_cfg.get("asr", {})
    if isinstance(asr_cfg, dict):
        backend = _backend_from_target(asr_cfg.get("backend", ""))
        if backend:
            selected.add(backend)
    return selected


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _aws_sts_preflight_enabled() -> bool:
    raw = os.getenv("WEB_GUI_SKIP_AWS_STS_PREFLIGHT", "").strip().lower()
    return raw not in {"1", "true", "yes", "on"}


def _aws_sts_preflight_ttl_sec() -> float:
    raw = os.getenv("WEB_GUI_AWS_STS_PREFLIGHT_TTL_SEC", "120").strip()
    try:
        ttl = float(raw)
    except ValueError:
        ttl = 120.0
    return max(0.0, min(ttl, 3600.0))


def _aws_sts_preflight_cache_key(env_merged: dict[str, str]) -> str:
    profile = str(env_merged.get("AWS_PROFILE", "")).strip()
    region = str(env_merged.get("AWS_REGION", "")).strip()
    access_key = str(env_merged.get("AWS_ACCESS_KEY_ID", "")).strip()
    token = str(env_merged.get("AWS_SESSION_TOKEN", "")).strip()
    config_path = str(env_merged.get("AWS_CONFIG_FILE", "")).strip()
    creds_path = str(env_merged.get("AWS_SHARED_CREDENTIALS_FILE", "")).strip()
    token_tail = token[-8:] if token else ""
    return "|".join(
        [
            f"profile={profile}",
            f"region={region}",
            f"access={access_key}",
            f"token={token_tail}",
            f"config={config_path}",
            f"creds={creds_path}",
        ]
    )


def _normalize_aws_auth_error(detail: str) -> str:
    text = str(detail or "").strip()
    lowered = text.lower()
    if "pending authorization" in lowered and "expired" in lowered:
        return (
            "AWS SSO authorization expired before completion. Run AWS SSO Login again and "
            "complete browser/device confirmation promptly."
        )
    if "invalidgrantexception" in lowered and "createtoken" in lowered:
        return (
            "AWS SSO token exchange failed (InvalidGrantException). Re-run AWS SSO Login and "
            "verify AWS_SSO_START_URL / AWS_SSO_REGION values."
        )
    if "invalid_grant" in lowered:
        return (
            "AWS SSO token exchange failed (invalid_grant). Re-run AWS SSO Login and "
            "complete the device/browser flow before code expiration."
        )
    if "error loading sso token" in lowered or (
        "token for" in lowered and "does not exist" in lowered
    ):
        return (
            "AWS SSO token is not present locally. Run AWS SSO Login to create/refresh "
            "the token cache for the selected profile."
        )
    if "unable to locate credentials" in lowered or "partial credentials found" in lowered:
        return (
            "AWS credentials are not available. Provide AWS_PROFILE or "
            "AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY."
        )
    if "token has expired" in lowered or "expired and refresh failed" in lowered:
        return "AWS credentials are expired. Refresh AWS auth (SSO/login token) and retry."
    return text


@contextmanager
def _temporary_env(overrides: dict[str, str]):
    previous: dict[str, str | None] = {}
    for key, value in overrides.items():
        if not value:
            continue
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _run_aws_sts_preflight_boto3(env_merged: dict[str, str]) -> None:
    import boto3
    from botocore.config import Config as BotoConfig

    profile = str(env_merged.get("AWS_PROFILE", "")).strip()
    region = str(env_merged.get("AWS_REGION", "")).strip()
    session_kwargs: dict[str, str] = {}
    if profile:
        session_kwargs["profile_name"] = profile
    if region:
        session_kwargs["region_name"] = region

    try:
        with _temporary_env(env_merged):
            session = boto3.Session(**session_kwargs)
            sts = session.client(
                "sts",
                region_name=region or None,
                config=BotoConfig(connect_timeout=5, read_timeout=8, retries={"max_attempts": 1}),
            )
            sts.get_caller_identity()
    except Exception as exc:
        detail = _normalize_aws_auth_error(str(exc).strip() or exc.__class__.__name__)
        raise HTTPException(status_code=400, detail=f"AWS auth preflight failed: {detail}") from exc


def _run_aws_sts_preflight_cli(env_merged: dict[str, str]) -> None:
    aws_cli = shutil.which("aws")
    if not aws_cli:
        raise HTTPException(
            status_code=400,
            detail="AWS backend selected but AWS CLI is not available in PATH.",
        )

    cmd = [aws_cli, "sts", "get-caller-identity", "--output", "json"]
    profile = str(env_merged.get("AWS_PROFILE", "")).strip()
    if profile:
        cmd.extend(["--profile", profile])

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, **env_merged},
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=400,
            detail="AWS auth preflight timed out while validating credentials.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"AWS auth preflight failed to start: {exc}",
        ) from exc

    if result.returncode == 0:
        return

    detail = (result.stderr or "").strip() or (result.stdout or "").strip()
    if not detail:
        detail = f"exit code {result.returncode}"
    detail = _normalize_aws_auth_error(detail)
    raise HTTPException(status_code=400, detail=f"AWS auth preflight failed: {detail}")


def _run_aws_sts_preflight(env_merged: dict[str, str]) -> None:
    ttl_sec = _aws_sts_preflight_ttl_sec()
    cache_key = _aws_sts_preflight_cache_key(env_merged)
    if ttl_sec > 0.0:
        expires_at = _AWS_STS_PREFLIGHT_CACHE.get(cache_key, 0.0)
        if expires_at > time.monotonic():
            return

    try:
        _run_aws_sts_preflight_boto3(env_merged)
    except ModuleNotFoundError:
        _run_aws_sts_preflight_cli(env_merged)
    if ttl_sec > 0.0:
        _AWS_STS_PREFLIGHT_CACHE[cache_key] = time.monotonic() + ttl_sec


def _validate_cloud_auth(
    *,
    payload: dict[str, Any],
    merged_cfg: dict[str, Any],
    env_merged: dict[str, str],
) -> None:
    selected = _requested_backends(payload, merged_cfg)

    if "google" in selected:
        google_cfg = _backend_cfg(merged_cfg, "google")
        creds_path = _first_non_empty(
            env_merged.get("GOOGLE_APPLICATION_CREDENTIALS"),
            google_cfg.get("credentials_json"),
        )
        if not creds_path:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Google backend selected but credentials are missing. "
                    "Set secret google_credentials_json or GOOGLE_APPLICATION_CREDENTIALS."
                ),
            )
        creds_file = Path(creds_path).expanduser()
        if not creds_file.exists() or not creds_file.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Google credentials file not found: {creds_file}",
            )
        try:
            with creds_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Google credentials file is not valid JSON: {creds_file}",
            ) from exc
        except OSError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Google credentials file is not readable: {creds_file}",
            ) from exc
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Google credentials file must contain JSON object: {creds_file}",
            )

    if "azure" in selected:
        azure_cfg = _backend_cfg(merged_cfg, "azure")
        key = _first_non_empty(env_merged.get("AZURE_SPEECH_KEY"), azure_cfg.get("speech_key"))
        region = _first_non_empty(env_merged.get("AZURE_SPEECH_REGION"), azure_cfg.get("region"))
        if bool(key) != bool(region):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Azure backend selected but auth is incomplete. "
                    "Provide both AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
                ),
            )
        if not key or not region:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Azure backend selected but credentials are missing. "
                    "Provide azure_speech_key and azure_region."
                ),
            )

    if "aws" in selected:
        aws_cfg = _backend_cfg(merged_cfg, "aws")
        profile = _first_non_empty(env_merged.get("AWS_PROFILE"), aws_cfg.get("profile"))
        access_key_id = _first_non_empty(
            env_merged.get("AWS_ACCESS_KEY_ID"),
            aws_cfg.get("access_key_id"),
        )
        secret_key = _first_non_empty(
            env_merged.get("AWS_SECRET_ACCESS_KEY"),
            aws_cfg.get("secret_access_key"),
        )
        bucket = _first_non_empty(env_merged.get("ASR_AWS_S3_BUCKET"), aws_cfg.get("s3_bucket"))
        if not bucket:
            raise HTTPException(
                status_code=400,
                detail="AWS backend selected but S3 bucket is missing (ASR_AWS_S3_BUCKET).",
            )
        if bool(access_key_id) != bool(secret_key):
            raise HTTPException(
                status_code=400,
                detail=(
                    "AWS backend selected but access key auth is incomplete. "
                    "Provide both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                ),
            )
        if not profile and not (access_key_id and secret_key):
            raise HTTPException(
                status_code=400,
                detail=(
                    "AWS backend selected but credentials are missing. "
                    "Provide AWS_PROFILE or access key pair."
                ),
            )

        config_file = str(env_merged.get("AWS_CONFIG_FILE", "")).strip()
        if config_file:
            config_path = Path(config_file).expanduser()
            if not config_path.exists() or not config_path.is_file():
                raise HTTPException(
                    status_code=400,
                    detail=f"AWS_CONFIG_FILE not found: {config_path}",
                )
            env_merged.setdefault("AWS_SDK_LOAD_CONFIG", "1")

        credentials_file = str(env_merged.get("AWS_SHARED_CREDENTIALS_FILE", "")).strip()
        if credentials_file:
            credentials_path = Path(credentials_file).expanduser()
            if not credentials_path.exists() or not credentials_path.is_file():
                raise HTTPException(
                    status_code=400,
                    detail=f"AWS_SHARED_CREDENTIALS_FILE not found: {credentials_path}",
                )

        if _aws_sts_preflight_enabled():
            _run_aws_sts_preflight(env_merged)


def _prepare_runtime(req: RunRequest) -> tuple[Path, dict[str, Any], dict[str, str]]:
    merged_secrets = {str(k): str(v) for k, v in req.secrets.items() if str(v).strip()}
    env_from_auth: dict[str, str] = {}
    if req.aws_auth_profile.strip():
        try:
            auth_ctx = resolve_auth_context(req.aws_auth_profile.strip())
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        for key, value in auth_ctx.runtime_secrets.items():
            merged_secrets.setdefault(key, value)
        env_from_auth.update(auth_ctx.env_extra)

    try:
        runtime_path, merged_cfg, env_secrets = build_runtime_config(
            base_config_path=req.base_config,
            runtime_overrides=req.runtime_overrides,
            secrets=merged_secrets,
            profile_name=req.profile_name,
        )
        env_merged = dict(env_secrets)
        env_merged.update(env_from_auth)
        _validate_cloud_auth(
            payload=req.payload,
            merged_cfg=merged_cfg,
            env_merged=env_merged,
        )
        return runtime_path, merged_cfg, env_merged
    except (ConfigBuildError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/")
def root() -> FileResponse:
    """Serve main frontend page."""
    return FileResponse(str(WEB_GUI_ROOT / "static" / "index.html"))


@app.get("/api/options")
def api_options() -> dict[str, Any]:
    """Return static option catalogs and default configs."""
    return get_options_payload()


@app.get("/api/aws-auth-profiles")
def api_aws_auth_profiles() -> dict[str, Any]:
    """List available text AWS auth profiles."""
    return {"profiles": list_auth_profiles()}


@app.get("/api/aws-auth-profiles/{name}")
def api_aws_auth_profile(name: str) -> dict[str, Any]:
    """Load one AWS auth profile from text file."""
    try:
        content, values = load_auth_profile(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"name": name, "content": content, "values": values}


@app.post("/api/aws-auth-profiles")
def api_save_aws_auth_profile(req: SaveAwsAuthProfileRequest) -> dict[str, Any]:
    """Save/update one AWS auth profile text file."""
    try:
        path = save_auth_profile(req.name, content=req.content, values=req.values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": str(path.resolve()),
        "profiles": list_auth_profiles(),
        "content": path.read_text(encoding="utf-8"),
    }


@app.post("/api/aws-sso-login")
def api_aws_sso_login(req: AwsSsoLoginRequest) -> dict[str, Any]:
    """Start AWS SSO login as background job for selected auth profile."""
    try:
        ctx = resolve_auth_context(req.auth_profile, for_login=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not str(ctx.values.get("AWS_SSO_START_URL", "")).strip() or not str(
        ctx.values.get("AWS_SSO_REGION", "")
    ).strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "AWS SSO login requires AWS_SSO_START_URL and AWS_SSO_REGION "
                "in selected auth profile."
            ),
        )

    # SSO login requires AWS CLI profile and local AWS_CONFIG_FILE prepared by context resolver.
    args = ["aws", "sso", "login", "--profile", ctx.profile_name]
    if req.no_browser:
        args.append("--no-browser")
    if req.use_device_code:
        args.append("--use-device-code")
    login_cmd = " ".join(shlex.quote(item) for item in args)
    shell = f"set -euo pipefail ; cd {shlex.quote(str(REPO_ROOT))} ; {login_cmd}"
    command = CommandSpec(
        shell_command=shell,
        display_command=login_cmd,
        metadata={
            "aws_auth_profile": req.auth_profile,
            "aws_auth_file": str(auth_profile_path(req.auth_profile)),
            "use_device_code": bool(req.use_device_code),
            "no_browser": bool(req.no_browser),
        },
    )
    job = JOBS.start_job(kind="aws_sso_login", command=command, env_extra=ctx.env_extra)
    return {
        "job": job.to_dict(),
        "profile": req.auth_profile,
        "content": dump_env_like_text(ctx.values),
    }


@app.get("/api/files")
def api_files() -> dict[str, Any]:
    """List uploaded/noisy/results files."""
    return {
        "uploads": list_uploads(),
        "noisy": list_noisy_samples(),
        "results": list_results(),
    }


@app.get("/api/preflight")
def api_preflight() -> dict[str, Any]:
    """Run environment readiness checks (deps/ROS/audio)."""
    return run_preflight_checks()


@app.post("/api/upload")
async def api_upload(file: UploadFile = UPLOAD_FILE_PARAM) -> dict[str, Any]:
    """Store uploaded sample/dataset/config file in GUI upload directory."""
    filename = Path(file.filename or "upload.bin").name
    if not filename:
        raise HTTPException(status_code=400, detail="Empty filename")
    destination = UPLOADS_DIR / filename
    content = await file.read()
    destination.write_bytes(content)
    return {"path": str(destination.resolve()), "size": len(content)}


@app.post("/api/noise/apply")
def api_noise_apply(req: NoiseRequest) -> dict[str, Any]:
    """Generate noisy sample variants for selected SNR values."""
    try:
        generated = apply_noise_levels(req.source_wav, req.snr_levels)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"generated": [str(item) for item in generated]}


@app.post("/api/profiles")
def api_save_profile(req: SaveProfileRequest) -> dict[str, Any]:
    """Persist frontend profile payload."""
    path = save_profile(req.name, req.payload)
    return {"path": str(path.resolve()), "profiles": list_profiles()}


@app.get("/api/profiles/{name}")
def api_load_profile(name: str) -> dict[str, Any]:
    """Load named frontend profile."""
    try:
        payload = load_profile(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"name": name, "payload": payload}


@app.post("/api/jobs/live-sample")
def api_run_live_sample(req: RunRequest) -> dict[str, Any]:
    """Start live-sample evaluation job."""
    validate_live_request(req.payload, req.runtime_overrides)
    runtime_path, merged_cfg, env_secrets = _prepare_runtime(req)
    command = build_live_sample_command(runtime_path, req.payload)
    job = JOBS.start_job(kind="live_sample", command=command, env_extra=env_secrets)
    return {
        "job": job.to_dict(),
        "runtime_config": str(runtime_path),
        "effective_config": merged_cfg,
    }


@app.post("/api/jobs/benchmark")
def api_run_benchmark(req: RunRequest) -> dict[str, Any]:
    """Start benchmark job."""
    validate_benchmark_request(req.payload, req.runtime_overrides)
    runtime_path, merged_cfg, env_secrets = _prepare_runtime(req)
    command = build_benchmark_command(runtime_path, req.payload)
    job = JOBS.start_job(kind="benchmark", command=command, env_extra=env_secrets)
    return {
        "job": job.to_dict(),
        "runtime_config": str(runtime_path),
        "effective_config": merged_cfg,
    }


@app.post("/api/jobs/ros-bringup")
def api_run_ros_bringup(req: RunRequest) -> dict[str, Any]:
    """Start long-running ROS2 bringup job."""
    validate_ros_bringup_request(req.payload, req.runtime_overrides)
    runtime_path, merged_cfg, env_secrets = _prepare_runtime(req)
    command = build_ros_bringup_command(runtime_path, req.payload)
    job = JOBS.start_job(
        kind="ros_bringup",
        command=command,
        env_extra=env_secrets,
        long_running=True,
    )
    return {
        "job": job.to_dict(),
        "runtime_config": str(runtime_path),
        "effective_config": merged_cfg,
    }


@app.get("/api/jobs")
def api_jobs(
    hide_inactive_restored: bool = Query(
        default=False,
        description="Hide inactive jobs restored from previous app sessions.",
    )
) -> dict[str, Any]:
    """List started jobs."""
    return {
        "jobs": [
            item.to_dict()
            for item in JOBS.list_jobs(hide_inactive_restored=hide_inactive_restored)
        ]
    }


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str) -> dict[str, Any]:
    """Get one job by id."""
    try:
        record = JOBS.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"job": record.to_dict()}


@app.get("/api/jobs/{job_id}/logs")
def api_job_logs(job_id: str, lines: int = Query(default=200, ge=1, le=5000)) -> dict[str, Any]:
    """Read tail of job log file."""
    try:
        log = JOBS.read_log_tail(job_id, lines=lines)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"job_id": job_id, "log": log}


@app.post("/api/jobs/{job_id}/stop")
def api_stop_job(job_id: str) -> dict[str, Any]:
    """Stop running process."""
    try:
        record = JOBS.stop_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"job": record.to_dict()}


@app.get("/api/artifacts")
def api_artifact(path: str = Query(...)) -> FileResponse:
    """Serve artifact file if it resides under allowed repository roots."""
    try:
        resolved = resolve_under_roots(path, roots=ALLOWED_ARTIFACT_ROOTS)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {resolved}")
    return FileResponse(str(resolved))


@app.exception_handler(Exception)
def api_unhandled(_: Any, exc: Exception) -> JSONResponse:
    """Generic fallback for unhandled errors."""
    LOGGER.exception("Unhandled API exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
