"""FastAPI server for ROS2 ASR Web GUI."""

from __future__ import annotations

import shlex
from contextlib import asynccontextmanager
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
    no_browser: bool = True


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
def api_jobs() -> dict[str, Any]:
    """List all started jobs."""
    return {"jobs": [item.to_dict() for item in JOBS.list_jobs()]}


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
    return JSONResponse(status_code=500, content={"detail": str(exc)})
