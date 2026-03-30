"""Gateway API server bridging GUI and ROS2/core layers."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
from collections import deque
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from asr_benchmark_core.noise import apply_noise_to_wav, resolve_noise_plan
from asr_config import (
    list_profiles,
    load_secret_ref,
    local_env_file_path,
    resolve_env_value,
    resolve_profile,
    resolve_secret_ref,
    validate_benchmark_payload,
    validate_metric_payload,
    validate_runtime_payload,
    write_local_env_values,
)
from asr_core import make_request_id, make_run_id, make_session_id
from asr_datasets import DatasetEntry, DatasetRegistry, import_from_uploaded_files, load_manifest
from asr_gateway.ros_client import GatewayRosClient
from asr_gateway.log_views import (
    collect_logs as collect_logs_helper,
    detect_severity as detect_severity_helper,
    log_files as log_files_helper,
    tail_lines as tail_lines_helper,
)
from asr_gateway.result_views import (
    compare_runs as compare_runs_helper,
    list_benchmark_history as list_benchmark_history_helper,
    metric_preference as metric_preference_helper,
    run_detail as run_detail_helper,
    run_dir as run_dir_helper,
)
from asr_gateway.runtime_assets import (
    list_runtime_samples as list_runtime_samples_helper,
    noise_output_target_for_snr,
    resolve_runtime_sample_path as resolve_runtime_sample_path_helper,
    runtime_upload_target as runtime_upload_target_helper,
    wav_metadata_from_bytes as wav_metadata_from_bytes_helper,
    wav_metadata_from_file as wav_metadata_from_file_helper,
)
from asr_gateway.secret_state import (
    aws_backend_from_current_env as aws_backend_from_current_env_helper,
    azure_secret_status as azure_secret_status_helper,
    google_secret_status as google_secret_status_helper,
    normalize_ref_name as normalize_ref_name_helper,
    secret_ref_path as secret_ref_path_helper,
    validate_secret_file as validate_secret_file_helper,
    mask_email as mask_email_helper,
)
from asr_metrics.quality import has_quality_reference
from asr_provider_base import ProviderAudio, ProviderManager, create_provider, list_providers
from asr_provider_base.catalog import (
    default_preset_id,
    provider_presets,
    provider_ui,
    resolve_provider_execution,
)
from asr_reporting import export_csv, export_json, export_markdown
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    import python_multipart  # type: ignore[import-not-found]  # noqa: F401
except ImportError:
    MULTIPART_AVAILABLE = False
else:
    MULTIPART_AVAILABLE = True

if MULTIPART_AVAILABLE:
    from fastapi import File, Form, UploadFile


PROFILE_TYPE_DIRS = {
    "runtime": "runtime",
    "providers": "providers",
    "benchmark": "benchmark",
    "datasets": "datasets",
    "metrics": "metrics",
    "deployment": "deployment",
    "gui": "gui",
}

HUMAN_PROVIDER_NAMES = {
    "whisper": "Whisper",
    "vosk": "Vosk",
    "azure": "Azure Speech",
    "google": "Google STT",
    "aws": "AWS Transcribe",
}

SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_./-]+$")
AWS_DEVICE_CODE_RE = re.compile(r"\b[A-Z0-9]{4}(?:-[A-Z0-9]{4})+\b")
AWS_URL_RE = re.compile(r"https?://[^\s<>()]+")


def _no_cache_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: dict[str, Any]) -> Any:
        response = await super().get_response(path, scope)
        for key, value in _no_cache_headers().items():
            response.headers[key] = value
        return response


def _aws_device_login_page_url(start_url: str) -> str:
    text = str(start_url or "").strip()
    if not text:
        return ""
    if "#/device" in text:
        return text
    normalized = text.rstrip("/")
    if normalized.endswith("/start"):
        return f"{normalized}/#/device"
    return text


def _extract_aws_login_job_hints(lines: list[str], *, start_url: str = "") -> dict[str, str]:
    normalized_start_url = str(start_url or "").strip()
    login_page_url = _aws_device_login_page_url(normalized_start_url)
    verification_uri = ""
    user_code = ""

    for raw in lines or []:
        line = str(raw or "").strip()
        if not line:
            continue

        if not user_code:
            match = AWS_DEVICE_CODE_RE.search(line.upper())
            if match:
                user_code = match.group(0)

        for raw_url in AWS_URL_RE.findall(line):
            url = raw_url.rstrip(".,")
            if "#/device" in url:
                login_page_url = url
            elif not verification_uri:
                verification_uri = url

            if not login_page_url and ".awsapps.com/start" in url:
                login_page_url = _aws_device_login_page_url(url)

    if not login_page_url and verification_uri:
        login_page_url = verification_uri

    return {
        "sso_start_url": normalized_start_url,
        "login_page_url": login_page_url,
        "verification_uri": verification_uri,
        "user_code": user_code,
    }


def _detect_project_root() -> Path:
    env_root = os.getenv("ASR_PROJECT_ROOT", "").strip()
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if (candidate / "configs").exists():
            return candidate

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "configs").exists() and (candidate / "datasets").exists():
            return candidate
    return cwd


PROJECT_ROOT = _detect_project_root()
# These paths let the gateway act as a single control point for configs,
# uploaded samples, artifacts, logs, and secret metadata.
CONFIGS_ROOT = PROJECT_ROOT / "configs"
SECRETS_REFS_ROOT = PROJECT_ROOT / "secrets" / "refs"
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"
LOGS_ROOT = PROJECT_ROOT / "logs"
DATASET_REGISTRY_PATH = PROJECT_ROOT / "datasets" / "registry" / "datasets.json"
RUNTIME_SAMPLES_ROOT = PROJECT_ROOT / "data" / "sample"
RUNTIME_SAMPLE_UPLOADS_ROOT = RUNTIME_SAMPLES_ROOT / "uploads"
RUNTIME_NOISE_ROOT = RUNTIME_SAMPLES_ROOT / "generated_noise"
RUNTIME_SAMPLE_SUFFIXES = {".wav", ".wave"}

# Lightweight in-memory state for recent UI history. Durable outputs still live
# on disk under artifacts/logs; these caches only serve fast dashboard polling.
_RUNTIME_EVENTS: deque[dict[str, Any]] = deque(maxlen=200)
_RUNTIME_RESULTS: deque[dict[str, Any]] = deque(maxlen=80)
_BENCHMARK_JOBS: dict[str, dict[str, Any]] = {}
_BENCHMARK_LOCK = threading.Lock()
_SECRET_LOGIN_JOBS: dict[str, dict[str, Any]] = {}
_SECRET_LOGIN_LOCK = threading.Lock()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    del app
    try:
        yield
    finally:
        close = getattr(ros, "close", None)
        if callable(close):
            close()


app = FastAPI(title="ASR Gateway", version="0.2.0", lifespan=_lifespan)
ros = GatewayRosClient(timeout_sec=5.0)
if (PROJECT_ROOT / "web_ui" / "frontend").exists():
    # Serve the static browser UI from the same process that exposes the API so
    # operators only need one host/port.
    app.mount(
        "/ui", NoCacheStaticFiles(directory=str(PROJECT_ROOT / "web_ui" / "frontend")), name="ui"
    )


# Pydantic request models define the JSON contract between browser/scripts and
# the gateway. They intentionally mirror the user-facing forms closely.
class RuntimeStartRequest(BaseModel):
    runtime_profile: str = "default_runtime"
    provider_profile: str = "providers/whisper_local"
    processing_mode: str = "segmented"
    provider_preset: str = ""
    provider_settings: dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""
    audio_source: str = "file"
    audio_file_path: str = "data/sample/vosk_test.wav"
    language: str = "en-US"
    mic_capture_sec: float = 4.0


class RuntimeStopRequest(BaseModel):
    session_id: str = ""


class RuntimeReconfigureRequest(BaseModel):
    session_id: str = ""
    runtime_profile: str = "default_runtime"
    provider_profile: str = "providers/whisper_local"
    processing_mode: str = "segmented"
    provider_preset: str = ""
    provider_settings: dict[str, Any] = Field(default_factory=dict)
    audio_source: str = "file"
    audio_file_path: str = "data/sample/vosk_test.wav"
    language: str = "en-US"
    mic_capture_sec: float = 4.0


class RecognizeRequest(BaseModel):
    wav_path: str
    language: str = "en-US"
    session_id: str = ""
    provider_profile: str = ""
    provider_preset: str = ""
    provider_settings: dict[str, Any] = Field(default_factory=dict)


class NoiseGenerateRequest(BaseModel):
    source_wav: str
    snr_levels: list[float] = Field(default_factory=list)


class BenchmarkRunRequest(BaseModel):
    benchmark_profile: str = "default_benchmark"
    dataset_profile: str = "sample_dataset"
    providers: list[str] = Field(default_factory=list)
    scenario: str = ""
    provider_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)
    benchmark_settings: dict[str, Any] = Field(default_factory=dict)
    run_id: str = ""


class DatasetRegisterRequest(BaseModel):
    manifest_path: str
    dataset_id: str
    dataset_profile: str = ""


class DatasetImportRequest(BaseModel):
    source_path: str
    dataset_id: str
    dataset_profile: str = ""


class DatasetValidateManifestRequest(BaseModel):
    manifest_path: str
    check_audio_files: bool = False


class ConfigValidateRequest(BaseModel):
    profile_type: str
    profile_id: str


class ProfileSaveRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    replace: bool = False


class ProviderProfileRequest(BaseModel):
    provider_profile: str
    provider_preset: str = ""
    provider_settings: dict[str, Any] = Field(default_factory=dict)


class ProviderTestRequest(BaseModel):
    provider_profile: str
    provider_preset: str = ""
    provider_settings: dict[str, Any] = Field(default_factory=dict)
    wav_path: str = "data/sample/vosk_test.wav"
    language: str = "en-US"


class SecretRefUpsertRequest(BaseModel):
    file_name: str
    ref_id: str
    provider: str
    kind: str
    path: str = ""
    env_fallback: str = ""
    required: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    masked: bool = True


class SecretValidateRequest(BaseModel):
    ref_name: str


class SecretLinkProviderRequest(BaseModel):
    provider_profile: str
    ref_name: str


class AwsSsoLoginStartRequest(BaseModel):
    ref_name: str = "aws_profile"
    profile: str = ""
    use_device_code: bool = True
    no_browser: bool = True


class AzureEnvSaveRequest(BaseModel):
    ref_name: str = "azure_speech_key"
    speech_key: str = ""
    region: str = ""
    endpoint: str = ""
    clear_speech_key: bool = False
    clear_region: bool = False
    clear_endpoint: bool = False


class SecretFileClearRequest(BaseModel):
    ref_name: str


class ResultCompareRequest(BaseModel):
    run_ids: list[str]
    metrics: list[str] = Field(default_factory=list)


class ResultExportRequest(BaseModel):
    run_ids: list[str]
    formats: list[str] = Field(default_factory=lambda: ["json", "csv", "md"])
    name: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_name(raw: str, what: str) -> str:
    value = str(raw or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{what} is required")
    if not SAFE_NAME_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {what}: {value}")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HTTPException(status_code=400, detail=f"Unsafe {what}: {value}")
    return value


def _normalize_profile_type(profile_type: str) -> str:
    normalized = str(profile_type or "").strip().lower()
    if normalized not in PROFILE_TYPE_DIRS:
        raise HTTPException(status_code=404, detail=f"Unknown profile type: {profile_type}")
    return normalized


def _normalize_profile_id(profile_type: str, profile_id: str) -> str:
    value = _clean_name(profile_id, "profile_id")
    if value.endswith(".yaml"):
        value = value[:-5]
    prefix = f"{profile_type}/"
    if value.startswith(prefix):
        value = value.split("/", 1)[1]
    return value


def _profile_path(profile_type: str, profile_id: str) -> tuple[Path, str]:
    ptype = _normalize_profile_type(profile_type)
    pid = _normalize_profile_id(ptype, profile_id)
    folder = CONFIGS_ROOT / PROFILE_TYPE_DIRS[ptype]
    path = folder / f"{pid}.yaml"
    if ".." in path.parts:
        raise HTTPException(status_code=400, detail="Unsafe profile path")
    return path, pid


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_provider_overrides(
    provider_overrides: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for profile, raw in (provider_overrides or {}).items():
        if not isinstance(raw, dict):
            continue
        settings = raw.get("settings", raw.get("provider_settings", {}))
        if not isinstance(settings, dict):
            settings = {}
        preset_id = str(raw.get("preset_id", raw.get("provider_preset", "")) or "").strip()
        normalized[str(profile)] = {
            "preset_id": preset_id,
            "settings": dict(settings),
        }
    return normalized


def _record_runtime_event(event: str, message: str, payload: dict[str, Any] | None = None) -> None:
    _RUNTIME_EVENTS.appendleft(
        {
            "event": event,
            "message": message,
            "time": _now_iso(),
            "payload": payload or {},
        }
    )


def _run_dir(run_id: str) -> Path:
    return run_dir_helper(ARTIFACTS_ROOT, run_id, clean_name=_clean_name)


def _session_dir(session_id: str) -> Path:
    sid = _clean_name(session_id, "session_id")
    return ARTIFACTS_ROOT / "runtime_sessions" / sid


def _project_relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def _wav_metadata_from_bytes(content: bytes) -> dict[str, Any]:
    return wav_metadata_from_bytes_helper(content)


def _wav_metadata_from_file(path: Path) -> dict[str, Any]:
    return wav_metadata_from_file_helper(path)


def _list_runtime_samples() -> dict[str, Any]:
    return list_runtime_samples_helper(
        samples_root=RUNTIME_SAMPLES_ROOT,
        uploads_root=RUNTIME_SAMPLE_UPLOADS_ROOT,
        project_relative_path=_project_relative_path,
        sample_suffixes=RUNTIME_SAMPLE_SUFFIXES,
        upload_enabled=MULTIPART_AVAILABLE,
    )


def _runtime_upload_target(filename: str) -> Path:
    return runtime_upload_target_helper(
        filename,
        uploads_root=RUNTIME_SAMPLE_UPLOADS_ROOT,
        sample_suffixes=RUNTIME_SAMPLE_SUFFIXES,
    )


def _resolve_runtime_sample_path(value: str, *, label: str = "sample_path") -> Path:
    return resolve_runtime_sample_path_helper(
        value,
        clean_name=_clean_name,
        project_root=PROJECT_ROOT,
        allowed_roots=(
            RUNTIME_SAMPLES_ROOT,
            ARTIFACTS_ROOT,
            PROJECT_ROOT / "results",
        ),
        label=label,
    )


def _noise_output_target(source: Path, snr_db: float) -> Path:
    return noise_output_target_for_snr(source, snr_db=snr_db, noise_root=RUNTIME_NOISE_ROOT)


def _module_ok(module_name: str) -> tuple[bool, str]:
    try:
        spec = importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        return False, f"Module not installed: {module_name}"
    return True, "ok"


def _check_microphone_stack() -> tuple[bool, str, dict[str, Any]]:
    details: dict[str, Any] = {}
    try:
        import sounddevice as sd  # type: ignore[import-not-found]
        import soundfile as sf  # type: ignore[import-not-found]

        details["sounddevice"] = getattr(sd, "__version__", "unknown")
        details["soundfile"] = getattr(sf, "__version__", "unknown")
        try:
            devices = sd.query_devices()
            default_in, _default_out = sd.default.device
            details["audio_device_count"] = len(devices)
            details["default_input"] = int(default_in) if default_in is not None else None
        except Exception as exc:  # pragma: no cover - device availability varies by environment
            return False, f"Audio device query failed: {exc}", details
        return True, "ok", details
    except Exception as exc:
        return False, str(exc), details


def _resolve_entrypoint_python(entrypoint: Path) -> tuple[str | None, str]:
    if not entrypoint.exists():
        return None, f"Entrypoint not found: {entrypoint}"
    try:
        first_line = (
            entrypoint.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        )
    except IndexError:
        return None, f"Entrypoint is empty: {entrypoint}"
    except Exception as exc:
        return None, f"Unable to read entrypoint: {exc}"

    if not first_line.startswith("#!"):
        return None, f"Entrypoint has no shebang: {entrypoint}"

    shebang = first_line[2:].strip()
    if not shebang:
        return None, f"Entrypoint shebang is empty: {entrypoint}"

    parts = shlex.split(shebang)
    if not parts:
        return None, f"Entrypoint shebang is invalid: {entrypoint}"

    if Path(parts[0]).name == "env":
        if len(parts) < 2:
            return None, f"Entrypoint env shebang is invalid: {entrypoint}"
        resolved = shutil.which(parts[1]) or parts[1]
        return resolved, f"shebang={shebang}"
    return parts[0], f"shebang={shebang}"


def _module_ok_via_python(python_exec: str | None, module_name: str) -> tuple[bool, str]:
    if not python_exec:
        return False, "Python executable is not defined"

    check_code = (
        "import importlib.util, sys; "
        f"sys.exit(0 if importlib.util.find_spec({module_name!r}) else 2)"
    )
    try:
        result = subprocess.run(
            [python_exec, "-c", check_code],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except FileNotFoundError:
        return False, f"Python executable not found: {python_exec}"
    except Exception as exc:
        return False, f"Unable to run module check with {python_exec}: {exc}"

    if result.returncode == 0:
        return True, f"{python_exec} imports {module_name}"

    details = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
    return False, f"{python_exec} cannot import {module_name}: {details}"


def _run_preflight_checks() -> dict[str, Any]:
    required_modules = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "soundfile": "soundfile",
        "sounddevice": "sounddevice",
        "faster_whisper": "faster_whisper",
        "vosk": "vosk",
        "google_cloud_speech": "google.cloud.speech",
        "boto3": "boto3",
        "azure_speech": "azure.cognitiveservices.speech",
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "psutil": "psutil",
        "yaml": "yaml",
    }

    module_checks: dict[str, dict[str, Any]] = {}
    for label, module_name in required_modules.items():
        ok, message = _module_ok(module_name)
        module_checks[label] = {"ok": ok, "message": message}

    ros_setup = Path("/opt/ros/jazzy/setup.bash")
    install_setup = PROJECT_ROOT / "ros2_ws" / "install" / "setup.bash"
    if not install_setup.exists():
        install_setup = PROJECT_ROOT / "install" / "setup.bash"

    ros_executable = shutil.which("ros2")
    mic_ok, mic_message, mic_details = _check_microphone_stack()

    gateway_exec = (
        install_setup.parent / "asr_gateway" / "lib" / "asr_gateway" / "asr_gateway_server"
    )
    runtime_exec = (
        install_setup.parent
        / "asr_runtime_nodes"
        / "lib"
        / "asr_runtime_nodes"
        / "asr_orchestrator_node"
    )
    benchmark_exec = (
        install_setup.parent
        / "asr_benchmark_nodes"
        / "lib"
        / "asr_benchmark_nodes"
        / "benchmark_manager_node"
    )
    runtime_python, runtime_python_message = _resolve_entrypoint_python(runtime_exec)
    runtime_whisper_ok, runtime_whisper_message = _module_ok_via_python(
        runtime_python, "faster_whisper"
    )

    checks = {
        "modules": module_checks,
        "microphone": {
            "ok": mic_ok,
            "message": mic_message,
            "details": mic_details,
        },
        "ros": {
            "ros2_binary": {
                "ok": bool(ros_executable or ros_setup.exists()),
                "message": ros_executable
                or "ros2 not in current PATH, but /opt/ros/jazzy/setup.bash is available",
            },
            "jazzy_setup": {
                "ok": ros_setup.exists(),
                "message": str(ros_setup),
            },
            "install_setup": {
                "ok": install_setup.exists(),
                "message": str(install_setup),
            },
            "gateway_node_installed": {
                "ok": gateway_exec.exists(),
                "message": str(gateway_exec),
            },
            "runtime_node_installed": {
                "ok": runtime_exec.exists(),
                "message": str(runtime_exec),
            },
            "benchmark_node_installed": {
                "ok": benchmark_exec.exists(),
                "message": str(benchmark_exec),
            },
            "runtime_python": {
                "ok": bool(runtime_python),
                "message": runtime_python_message,
            },
            "runtime_faster_whisper": {
                "ok": runtime_whisper_ok,
                "message": runtime_whisper_message,
            },
        },
    }

    ok = True
    for group in checks.values():
        if isinstance(group, dict):
            for item in group.values():
                if isinstance(item, dict) and "ok" in item and not bool(item["ok"]):
                    ok = False

    return {
        "ok": ok,
        "checks": checks,
    }


def _runtime_status() -> dict[str, Any]:
    result = ros.get_runtime_status()
    snapshot = ros.runtime_snapshot()
    if not result.success:
        active_session = snapshot.get("active_session", {})
        return {
            "available": False,
            "state": "unavailable",
            "message": result.message,
            "backend": "",
            "session_id": active_session.get("session_id", ""),
            "session_state": active_session.get("state", "unknown"),
            "capabilities": [],
            "streaming_supported": False,
            "streaming_mode": "none",
            "processing_mode": active_session.get("processing_mode", "segmented"),
            "audio_source": "",
            "runtime_profile": active_session.get("profile_id", ""),
            "observer_error": snapshot.get("observer_error", ""),
        }
    payload = _normalize_runtime_status_payload(snapshot, result.payload)
    payload["available"] = True
    payload["state"] = str(payload.get("session_state", payload.get("status_message", "unknown")))
    payload["message"] = "ok"
    payload["observer_error"] = snapshot.get("observer_error", "")
    return payload


def _audio_input_completion(snapshot: dict[str, Any], session_id: str) -> tuple[bool, str]:
    clean_session_id = str(session_id or "").strip()
    for item in list(snapshot.get("node_statuses", [])):
        if str(item.get("node_name", "") or "") != "audio_input_node":
            continue
        status_message = str(item.get("status_message", "") or "")
        if clean_session_id and f"session={clean_session_id}" not in status_message:
            continue
        if status_message.startswith("completed"):
            return True, status_message
    return False, ""


def _normalize_runtime_status_payload(
    snapshot: dict[str, Any], payload: dict[str, Any]
) -> dict[str, Any]:
    normalized = dict(payload)
    session_id = str(
        normalized.get("session_id", "")
        or snapshot.get("active_session", {}).get("session_id", "")
        or ""
    )
    audio_source = str(
        normalized.get("audio_source", "")
        or snapshot.get("active_session", {}).get("audio_source", "")
        or ""
    )
    is_completed, completion_message = _audio_input_completion(snapshot, session_id)
    if is_completed and audio_source == "file":
        normalized["session_state"] = "completed"
        normalized["status_message"] = completion_message or "completed source=file"
    return normalized


def _normalize_runtime_session_snapshot(
    snapshot: dict[str, Any], *, audio_source: str
) -> dict[str, Any]:
    normalized = {
        "recent_results": _merge_runtime_results(
            snapshot.get("recent_results", []), list(_RUNTIME_RESULTS)
        ),
        "recent_partials": list(snapshot.get("recent_partials", [])),
        "node_statuses": list(snapshot.get("node_statuses", [])),
        "session_statuses": [dict(item) for item in list(snapshot.get("session_statuses", []))],
        "active_session": dict(snapshot.get("active_session", {})),
    }
    if audio_source != "file":
        return normalized

    active_session_id = str(normalized["active_session"].get("session_id", "") or "")
    is_completed, completion_message = _audio_input_completion(snapshot, active_session_id)
    if not is_completed:
        return normalized

    if active_session_id:
        normalized["active_session"]["state"] = "completed"
        normalized["active_session"]["status_message"] = (
            completion_message or "completed source=file"
        )
        for item in normalized["session_statuses"]:
            if str(item.get("session_id", "") or "") == active_session_id:
                item["state"] = "completed"
                item["status_message"] = completion_message or "completed source=file"
    return normalized


def _merge_runtime_results(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for item in group:
            request_id = str(item.get("request_id", "") or "")
            key = (
                request_id,
                str(item.get("type", "final") or "final"),
                str(item.get("time", "") or ""),
            )
            if request_id:
                key = (request_id, str(item.get("type", "final") or "final"), "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    merged.sort(key=lambda item: str(item.get("time", "")), reverse=True)
    return merged


def _capabilities_to_dict(caps: Any) -> dict[str, Any]:
    return {
        "supports_streaming": bool(caps.supports_streaming),
        "streaming_mode": str(getattr(caps, "streaming_mode", "none") or "none"),
        "supports_batch": bool(caps.supports_batch),
        "supports_word_timestamps": bool(caps.supports_word_timestamps),
        "supports_partials": bool(caps.supports_partials),
        "supports_confidence": bool(caps.supports_confidence),
        "supports_language_auto_detect": bool(caps.supports_language_auto_detect),
        "supports_cpu": bool(caps.supports_cpu),
        "supports_gpu": bool(caps.supports_gpu),
        "requires_network": bool(caps.requires_network),
        "cost_model_type": str(caps.cost_model_type),
        "max_session_seconds": int(caps.max_session_seconds),
        "max_audio_seconds": int(caps.max_audio_seconds),
    }


def _provider_capabilities(provider_id: str) -> dict[str, Any]:
    try:
        adapter = create_provider(provider_id)
        return _capabilities_to_dict(adapter.discover_capabilities())
    except Exception:
        requires_network = provider_id in {"azure", "google", "aws"}
        return {
            "supports_streaming": False,
            "streaming_mode": "none",
            "supports_batch": False,
            "supports_word_timestamps": False,
            "supports_partials": False,
            "supports_confidence": False,
            "supports_language_auto_detect": False,
            "supports_cpu": True,
            "supports_gpu": False,
            "requires_network": requires_network,
            "cost_model_type": "unknown",
            "max_session_seconds": 0,
            "max_audio_seconds": 0,
        }


def _profile_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _validate_profile(profile_type: str, profile_id: str) -> tuple[bool, str]:
    ptype = _normalize_profile_type(profile_type)
    pid = _normalize_profile_id(ptype, profile_id)
    try:
        resolved = resolve_profile(
            profile_type=ptype, profile_id=pid, configs_root=str(CONFIGS_ROOT)
        )
        if ptype == "runtime":
            errors = validate_runtime_payload(resolved.data)
            if errors:
                return False, "; ".join(errors)
        if ptype == "benchmark":
            errors = validate_benchmark_payload(resolved.data)
            if errors:
                return False, "; ".join(errors)
        if ptype == "metrics":
            errors = validate_metric_payload(resolved.data)
            if errors:
                return False, "; ".join(errors)
        return True, "valid"
    except Exception as exc:
        return False, str(exc)


def _profile_links(profile_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if profile_type == "runtime":
        orchestrator = (
            payload.get("orchestrator", {}) if isinstance(payload.get("orchestrator"), dict) else {}
        )
        return {
            "provider_profile": orchestrator.get("provider_profile", ""),
            "language": orchestrator.get("language", ""),
        }
    if profile_type == "providers":
        return {
            "provider_id": payload.get("provider_id", ""),
            "credentials_ref": payload.get("credentials_ref", ""),
        }
    if profile_type == "benchmark":
        return {
            "dataset_profile": payload.get("dataset_profile", ""),
            "providers": payload.get("providers", []),
            "metric_profiles": payload.get("metric_profiles", []),
        }
    if profile_type == "datasets":
        return {
            "dataset_id": payload.get("dataset_id", ""),
            "manifest_path": payload.get("manifest_path", ""),
        }
    if profile_type == "metrics":
        return {
            "metrics": payload.get("metrics", []),
        }
    return {}


def _profile_summaries(profile_type: str) -> list[dict[str, Any]]:
    ptype = _normalize_profile_type(profile_type)
    summaries: list[dict[str, Any]] = []
    for profile_id in list_profiles(ptype, configs_root=str(CONFIGS_ROOT)):
        path, pid = _profile_path(ptype, profile_id)
        payload: dict[str, Any] = {}
        load_error = ""
        try:
            payload = _read_yaml(path)
        except Exception as exc:
            load_error = str(exc)

        valid, validation_message = _validate_profile(ptype, pid)
        if load_error:
            valid = False
            validation_message = load_error

        summaries.append(
            {
                "profile_id": pid,
                "profile_type": ptype,
                "path": str(path),
                "last_modified": _profile_mtime(path),
                "valid": valid,
                "validation_message": validation_message,
                "links": _profile_links(ptype, payload),
            }
        )
    return summaries


def _provider_profiles_summary() -> list[dict[str, Any]]:
    manager = ProviderManager(configs_root=str(CONFIGS_ROOT))
    result: list[dict[str, Any]] = []
    for profile_id in list_profiles("providers", configs_root=str(CONFIGS_ROOT)):
        path, pid = _profile_path("providers", profile_id)
        payload = _read_yaml(path)
        provider_id = str(payload.get("provider_id", "")).strip()
        credentials_ref = str(payload.get("credentials_ref", "")).strip()
        capabilities = _provider_capabilities(provider_id) if provider_id else {}
        execution = resolve_provider_execution(payload)
        presets = provider_presets(payload)
        ui = provider_ui(payload)

        valid = True
        message = "valid"
        status = "unknown"
        try:
            adapter = manager.create_from_profile(f"providers/{pid}")
            adapter_status = adapter.get_status()
            status = adapter_status.state
            capabilities = _capabilities_to_dict(adapter.discover_capabilities())
            adapter.teardown()
        except Exception as exc:
            valid = False
            message = str(exc)
            status = "invalid"

        result.append(
            {
                "provider_profile": pid,
                "provider_id": provider_id,
                "credentials_ref": credentials_ref,
                "valid": valid,
                "message": message,
                "status": status,
                "last_modified": _profile_mtime(path),
                "capabilities": capabilities,
                "settings": payload.get("settings", {}),
                "default_preset": default_preset_id(payload),
                "model_presets": presets,
                "execution_preview": execution,
                "ui": ui,
            }
        )
    return result


def _provider_catalog() -> list[dict[str, Any]]:
    declared = set(list_providers())
    dynamic = ros.list_backends()
    if dynamic.success:
        declared.update(dynamic.payload.get("provider_ids", []))

    by_profile: dict[str, int] = {}
    for row in _provider_profiles_summary():
        provider_id = str(row.get("provider_id", "")).strip()
        if provider_id:
            by_profile[provider_id] = by_profile.get(provider_id, 0) + 1

    catalog: list[dict[str, Any]] = []
    for provider_id in sorted(declared):
        caps = _provider_capabilities(provider_id)
        is_cloud = bool(caps.get("requires_network"))
        catalog.append(
            {
                "provider_id": provider_id,
                "name": HUMAN_PROVIDER_NAMES.get(provider_id, provider_id.title()),
                "kind": "cloud" if is_cloud else "local",
                "requires_credentials": bool(caps.get("requires_network")),
                "capabilities": caps,
                "profiles_count": by_profile.get(provider_id, 0),
                "status": "configured" if by_profile.get(provider_id, 0) > 0 else "not_configured",
            }
        )
    return catalog


def _normalize_ref_name(ref_name: str) -> str:
    return normalize_ref_name_helper(ref_name, clean_name=_clean_name)


def _secret_ref_path(ref_name: str) -> Path:
    return secret_ref_path_helper(
        ref_name,
        secrets_refs_root=SECRETS_REFS_ROOT,
        clean_name=_clean_name,
    )


def _aws_backend_from_current_env() -> Any:
    return aws_backend_from_current_env_helper(
        secret_ref_source=str(_secret_ref_path("aws_profile")),
        resolve_env_value=resolve_env_value,
    )


def _azure_secret_status(ref_source_path: str) -> dict[str, Any]:
    return azure_secret_status_helper(
        ref_source_path,
        resolve_env_value=resolve_env_value,
        local_env_file_path=local_env_file_path,
    )


def _mask_email(value: str) -> str:
    return mask_email_helper(value)


def _google_secret_status(
    ref_source_path: str, resolved_file_path: str = "", resolved_source: str = ""
) -> dict[str, Any]:
    return google_secret_status_helper(
        ref_source_path,
        resolved_file_path=resolved_file_path,
        resolved_source=resolved_source,
    )


def _apply_process_env(updates: dict[str, str], unset: list[str] | None = None) -> None:
    for key in unset or []:
        os.environ.pop(key, None)
    for key, value in updates.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)


def _aws_login_job_snapshot(job_id: str) -> dict[str, Any]:
    with _SECRET_LOGIN_LOCK:
        job = _SECRET_LOGIN_JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"AWS login job not found: {job_id}")
        validation = dict(job.get("validation", {}))
        auth = validation.get("auth", {}) if isinstance(validation.get("auth"), dict) else {}
        hints = _extract_aws_login_job_hints(
            list(job.get("lines", [])),
            start_url=str(job.get("sso_start_url") or auth.get("sso_start_url") or ""),
        )
        return {
            "job_id": job["job_id"],
            "kind": job.get("kind", "aws_sso_login"),
            "provider": "aws",
            "ref_name": job["ref_name"],
            "profile": job["profile"],
            "state": job["state"],
            "started_at": job["started_at"],
            "completed_at": job.get("completed_at", ""),
            "return_code": job.get("return_code"),
            "lines": list(job.get("lines", [])),
            "command": list(job.get("command", [])),
            "validation": validation,
            **hints,
        }


def _watch_aws_login_job(job_id: str, process: subprocess.Popen[str], ref_name: str) -> None:
    lines: deque[str] = deque(maxlen=200)
    try:
        if process.stdout is not None:
            for raw in process.stdout:
                line = str(raw).rstrip()
                if not line:
                    continue
                lines.append(line)
                with _SECRET_LOGIN_LOCK:
                    if job_id in _SECRET_LOGIN_JOBS:
                        _SECRET_LOGIN_JOBS[job_id]["lines"] = list(lines)
        return_code = process.wait()
        validation = _validate_secret_file(_secret_ref_path(ref_name))
        with _SECRET_LOGIN_LOCK:
            if job_id in _SECRET_LOGIN_JOBS:
                state = _SECRET_LOGIN_JOBS[job_id].get("state", "running")
                _SECRET_LOGIN_JOBS[job_id]["lines"] = list(lines)
                _SECRET_LOGIN_JOBS[job_id]["return_code"] = int(return_code)
                _SECRET_LOGIN_JOBS[job_id]["completed_at"] = _now_iso()
                if state != "cancelled":
                    _SECRET_LOGIN_JOBS[job_id]["state"] = (
                        "completed" if return_code == 0 else "failed"
                    )
                _SECRET_LOGIN_JOBS[job_id]["validation"] = validation
                _SECRET_LOGIN_JOBS[job_id].pop("_process", None)
    except Exception as exc:
        with _SECRET_LOGIN_LOCK:
            if job_id in _SECRET_LOGIN_JOBS:
                lines.append(str(exc))
                _SECRET_LOGIN_JOBS[job_id]["lines"] = list(lines)
                _SECRET_LOGIN_JOBS[job_id]["return_code"] = -1
                _SECRET_LOGIN_JOBS[job_id]["completed_at"] = _now_iso()
                _SECRET_LOGIN_JOBS[job_id]["state"] = "failed"
                _SECRET_LOGIN_JOBS[job_id]["validation"] = _validate_secret_file(
                    _secret_ref_path(ref_name)
                )
                _SECRET_LOGIN_JOBS[job_id].pop("_process", None)


def _start_aws_login_job(
    *,
    ref_name: str,
    profile: str,
    use_device_code: bool,
    no_browser: bool,
) -> dict[str, Any]:
    existing_running = None
    with _SECRET_LOGIN_LOCK:
        for job in _SECRET_LOGIN_JOBS.values():
            if job.get("profile") == profile and job.get("state") == "running":
                existing_running = job["job_id"]
                break
    if existing_running:
        return _aws_login_job_snapshot(existing_running)

    command = ["aws", "sso", "login", "--profile", profile]
    if no_browser:
        command.append("--no-browser")
    if use_device_code:
        command.append("--use-device-code")

    env = dict(os.environ)
    backend = _aws_backend_from_current_env()
    if backend.config_file:
        env["AWS_CONFIG_FILE"] = backend.config_file
    if backend.shared_credentials_file:
        env["AWS_SHARED_CREDENTIALS_FILE"] = backend.shared_credentials_file

    try:
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AWS CLI is not installed or not on PATH: {exc}",
        ) from exc
    job_id = make_request_id()
    with _SECRET_LOGIN_LOCK:
        _SECRET_LOGIN_JOBS[job_id] = {
            "job_id": job_id,
            "kind": "aws_sso_login",
            "provider": "aws",
            "ref_name": ref_name,
            "profile": profile,
            "state": "running",
            "started_at": _now_iso(),
            "completed_at": "",
            "return_code": None,
            "lines": [],
            "command": command,
            "validation": {},
            "_process": process,
        }
    thread = threading.Thread(
        target=_watch_aws_login_job,
        args=(job_id, process, ref_name),
        name=f"aws-sso-login-{profile}",
        daemon=True,
    )
    thread.start()
    return _aws_login_job_snapshot(job_id)


def _validate_secret_file(path: Path) -> dict[str, Any]:
    return validate_secret_file_helper(
        path,
        load_secret_ref=load_secret_ref,
        resolve_secret_ref=resolve_secret_ref,
        resolve_env_value=resolve_env_value,
        aws_backend_factory=_aws_backend_from_current_env,
        azure_status_factory=_azure_secret_status,
        google_status_factory=_google_secret_status,
    )


def _normalize_provider_profile(profile: str) -> str:
    clean = str(profile).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="provider_profile is required")
    return clean if clean.startswith("providers/") else f"providers/{clean}"


def _normalize_runtime_profile(profile: str) -> str:
    clean = str(profile).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="runtime_profile is required")
    return clean.split("/", 1)[1] if clean.startswith("runtime/") else clean


def _provider_execution_payload(
    profile: str,
    *,
    preset_id: str = "",
    settings_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = _normalize_provider_profile(profile)
    manager = ProviderManager(configs_root=str(CONFIGS_ROOT))
    payload = manager.resolve_profile_payload(normalized)
    execution = resolve_provider_execution(
        payload,
        preset_id=preset_id,
        settings_overrides=settings_overrides or {},
    )
    adapter = manager.create_from_profile(
        normalized,
        preset_id=str(execution.get("selected_preset", "") or ""),
        settings_overrides=dict(settings_overrides or {}),
    )
    try:
        capabilities = _capabilities_to_dict(adapter.discover_capabilities())
    finally:
        adapter.teardown()
    return {
        "normalized_profile": normalized,
        "payload": payload,
        "execution": execution,
        "capabilities": capabilities,
    }


def _preflight_provider_profile(
    profile: str,
    *,
    preset_id: str = "",
    settings_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _provider_execution_payload(
        profile,
        preset_id=preset_id,
        settings_overrides=settings_overrides,
    )


def _preflight_runtime_request(
    *,
    runtime_profile: str,
    provider_profile: str,
    provider_preset: str = "",
    provider_settings: dict[str, Any] | None = None,
    processing_mode: str = "",
    audio_source: str = "",
    audio_file_path: str = "",
    language: str = "",
    mic_capture_sec: float = 0.0,
) -> dict[str, Any]:
    runtime_profile_id = _normalize_runtime_profile(runtime_profile)
    try:
        resolved_runtime = resolve_profile(
            profile_type="runtime",
            profile_id=runtime_profile_id,
            configs_root=str(CONFIGS_ROOT),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    runtime_payload = deepcopy(resolved_runtime.data)
    if not isinstance(runtime_payload, dict):
        raise HTTPException(
            status_code=400,
            detail=f"Runtime profile `{runtime_profile_id}` must resolve to an object.",
        )

    audio_cfg = (
        dict(runtime_payload.get("audio", {}))
        if isinstance(runtime_payload.get("audio"), dict)
        else {}
    )
    orchestrator_cfg = (
        dict(runtime_payload.get("orchestrator", {}))
        if isinstance(runtime_payload.get("orchestrator"), dict)
        else {}
    )
    runtime_payload["audio"] = audio_cfg
    runtime_payload["orchestrator"] = orchestrator_cfg

    try:
        provider_exec = _preflight_provider_profile(
            provider_profile,
            preset_id=provider_preset,
            settings_overrides=provider_settings,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if str(audio_source or "").strip():
        audio_cfg["source"] = str(audio_source).strip()
    if str(processing_mode or "").strip():
        orchestrator_cfg["processing_mode"] = str(processing_mode).strip()
    if str(language or "").strip():
        orchestrator_cfg["language"] = str(language).strip()
    if float(mic_capture_sec or 0.0) > 0.0:
        audio_cfg["mic_capture_sec"] = float(mic_capture_sec)

    orchestrator_cfg["provider_profile"] = provider_exec["normalized_profile"]

    effective_audio_source = str(audio_cfg.get("source", "file") or "file").strip() or "file"
    effective_audio_file_path = str(audio_cfg.get("file_path", "") or "").strip()
    if effective_audio_source == "file":
        if str(audio_file_path or "").strip():
            effective_audio_file_path = str(audio_file_path).strip()
        if effective_audio_source == "file" and not effective_audio_file_path:
            raise HTTPException(
                status_code=400,
                detail="audio_file_path is required when audio_source=file",
            )
        if effective_audio_file_path:
            resolved_audio = _resolve_runtime_sample_path(
                effective_audio_file_path,
                label="audio_file_path",
            )
            if not resolved_audio.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Runtime WAV not found: {effective_audio_file_path}",
                )
            audio_cfg["file_path"] = _project_relative_path(resolved_audio)
            effective_audio_file_path = audio_cfg["file_path"]
    else:
        audio_cfg["file_path"] = ""
        effective_audio_file_path = ""

    errors = validate_runtime_payload(runtime_payload)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    if effective_audio_source == "mic":
        mic_ok, mic_message, _mic_details = _check_microphone_stack()
        if not mic_ok:
            raise HTTPException(
                status_code=400,
                detail=f"Microphone input is not available: {mic_message}",
            )

    effective_processing_mode = str(
        orchestrator_cfg.get("processing_mode", "segmented") or "segmented"
    ).strip()
    if effective_processing_mode == "provider_stream" and not bool(
        provider_exec["capabilities"].get("supports_streaming", False)
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Provider profile `{provider_exec['normalized_profile']}` does not support "
                "processing_mode=provider_stream"
            ),
        )

    return {
        "runtime_profile": runtime_profile_id,
        "provider_exec": provider_exec,
        "processing_mode": effective_processing_mode,
        "audio_source": effective_audio_source,
        "audio_file_path": effective_audio_file_path,
        "language": str(orchestrator_cfg.get("language", "") or "").strip(),
        "mic_capture_sec": float(audio_cfg.get("mic_capture_sec", 0.0) or 0.0),
        "resolved_config_ref": str(getattr(resolved_runtime, "snapshot_path", "") or ""),
    }


def _normalize_benchmark_profile(profile: str) -> str:
    clean = str(profile).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="benchmark_profile is required")
    return clean.split("/", 1)[1] if clean.startswith("benchmark/") else clean


def _normalize_dataset_profile(profile: str) -> str:
    clean = str(profile).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="dataset_profile is required")
    return clean if clean.startswith("datasets/") else f"datasets/{clean}"


def _quality_metrics_enabled(metric_names: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(metric_name in {"wer", "cer", "sample_accuracy"} for metric_name in metric_names)


def _default_benchmark_metrics() -> list[str]:
    return [
        "wer",
        "cer",
        "sample_accuracy",
        "total_latency_ms",
        "per_utterance_latency_ms",
        "real_time_factor",
        "success_rate",
        "failure_rate",
    ]


def _validate_dataset_quality_references(
    *,
    manifest_path: str,
    enabled_metrics: list[str] | tuple[str, ...] | set[str],
) -> None:
    if not _quality_metrics_enabled(enabled_metrics):
        return

    manifest_ref = Path(manifest_path)
    if not manifest_ref.is_absolute():
        manifest_ref = PROJECT_ROOT / manifest_ref
    samples = load_manifest(str(manifest_ref))
    invalid_sample_ids = [
        str(sample.sample_id)
        for sample in samples
        if not has_quality_reference(str(sample.transcript or ""))
    ]
    if not invalid_sample_ids:
        return

    preview = ", ".join(invalid_sample_ids[:8])
    if len(invalid_sample_ids) > 8:
        preview += f" (+{len(invalid_sample_ids) - 8} more)"
    raise HTTPException(
        status_code=400,
        detail=(
            "Benchmark quality metrics require non-empty normalized reference transcripts. "
            f"Invalid samples: {preview}"
        ),
    )


def _preflight_benchmark_request(req: BenchmarkRunRequest) -> dict[str, Any]:
    benchmark_profile_id = _normalize_benchmark_profile(req.benchmark_profile)
    try:
        benchmark_cfg = resolve_profile(
            profile_type="benchmark",
            profile_id=benchmark_profile_id,
            configs_root=str(CONFIGS_ROOT),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    benchmark_payload = deepcopy(benchmark_cfg.data)
    if not isinstance(benchmark_payload, dict):
        raise HTTPException(
            status_code=400,
            detail=f"Benchmark profile `{benchmark_profile_id}` must resolve to an object.",
        )

    errors = validate_benchmark_payload(benchmark_payload)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Benchmark profile validation failed: {'; '.join(errors)}",
        )

    dataset_profile = _normalize_dataset_profile(
        req.dataset_profile or str(benchmark_payload.get("dataset_profile", "") or "")
    )
    dataset_profile_id = dataset_profile.split("/", 1)[1]
    try:
        dataset_cfg = resolve_profile(
            profile_type="datasets",
            profile_id=dataset_profile_id,
            configs_root=str(CONFIGS_ROOT),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    manifest_path = str(dataset_cfg.data.get("manifest_path", "") or "").strip()
    if not manifest_path:
        raise HTTPException(status_code=400, detail="Dataset profile is missing manifest_path")

    metric_profiles = benchmark_payload.get("metric_profiles", [])
    enabled_metrics: list[str] = []
    if isinstance(metric_profiles, list):
        for metric_profile in metric_profiles:
            metric_ref = str(metric_profile or "").strip()
            if not metric_ref:
                continue
            metric_id = (
                metric_ref.split("/", 1)[1] if metric_ref.startswith("metrics/") else metric_ref
            )
            try:
                resolved_metric = resolve_profile(
                    profile_type="metrics",
                    profile_id=metric_id,
                    configs_root=str(CONFIGS_ROOT),
                )
                errors = validate_metric_payload(resolved_metric.data)
                if errors:
                    raise HTTPException(status_code=400, detail="; ".join(errors))
                enabled_metrics.extend(
                    [
                        str(metric_name).strip()
                        for metric_name in resolved_metric.data.get("metrics", [])
                        if str(metric_name or "").strip()
                    ]
                )
            except Exception as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    enabled_metrics = sorted(set(enabled_metrics)) or _default_benchmark_metrics()

    _validate_dataset_quality_references(
        manifest_path=manifest_path,
        enabled_metrics=enabled_metrics,
    )

    selected_providers = req.providers or [
        str(item).strip()
        for item in benchmark_payload.get("providers", [])
        if str(item or "").strip()
    ]
    normalized_providers = [_normalize_provider_profile(item) for item in selected_providers]
    if not normalized_providers:
        raise HTTPException(status_code=400, detail="No providers selected for benchmark run")

    normalized_overrides: dict[str, dict[str, Any]] = {}
    for profile, override in _normalize_provider_overrides(req.provider_overrides).items():
        normalized_overrides[_normalize_provider_profile(profile)] = dict(override)

    unexpected_overrides = sorted(set(normalized_overrides) - set(normalized_providers))
    if unexpected_overrides:
        raise HTTPException(
            status_code=400,
            detail=(
                "provider_overrides contains profiles that are not selected: "
                + ", ".join(unexpected_overrides)
            ),
        )

    merged_settings = _deep_merge(
        {
            "execution_mode": str(benchmark_payload.get("execution_mode", "batch") or "batch"),
            "batch": dict(benchmark_payload.get("batch", {}))
            if isinstance(benchmark_payload.get("batch"), dict)
            else {},
            "streaming": dict(benchmark_payload.get("streaming", {}))
            if isinstance(benchmark_payload.get("streaming"), dict)
            else {},
            "noise": dict(benchmark_payload.get("noise", {}))
            if isinstance(benchmark_payload.get("noise"), dict)
            else {},
        },
        dict(req.benchmark_settings or {}),
    )
    execution_mode = (
        str(merged_settings.get("execution_mode", "batch") or "batch").strip() or "batch"
    )
    if execution_mode not in {"batch", "streaming"}:
        raise HTTPException(
            status_code=400,
            detail="execution_mode must be one of: batch, streaming",
        )

    scenario = str(req.scenario or "").strip() or str(
        (benchmark_payload.get("scenarios") or ["clean_baseline"])[0]
    )
    try:
        resolve_noise_plan(
            scenario=scenario,
            benchmark_settings=merged_settings,
            profile_scenarios=[str(item) for item in benchmark_payload.get("scenarios", [])],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for provider_profile in normalized_providers:
        override = normalized_overrides.get(provider_profile, {})
        try:
            provider_exec = _preflight_provider_profile(
                provider_profile,
                preset_id=str(override.get("preset_id", "") or ""),
                settings_overrides=dict(override.get("settings", {}))
                if isinstance(override.get("settings", {}), dict)
                else {},
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if execution_mode == "streaming" and not bool(
            provider_exec["capabilities"].get("supports_streaming", False)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Provider does not support streaming benchmark mode: "
                    f"{provider_exec['normalized_profile']}"
                ),
            )

    return {
        "benchmark_profile": benchmark_profile_id,
        "dataset_profile": dataset_profile,
        "providers": normalized_providers,
        "provider_overrides": normalized_overrides,
        "benchmark_settings": merged_settings,
        "scenario": scenario,
    }


def _secret_ref_list() -> list[dict[str, Any]]:
    SECRETS_REFS_ROOT.mkdir(parents=True, exist_ok=True)
    linked: dict[str, list[str]] = {}
    for profile_id in list_profiles("providers", configs_root=str(CONFIGS_ROOT)):
        path, pid = _profile_path("providers", profile_id)
        payload = _read_yaml(path)
        cref = str(payload.get("credentials_ref", "")).strip()
        if cref:
            cref_path = Path(cref)
            if not cref_path.is_absolute():
                cref_path = (CONFIGS_ROOT.parent / cref_path).resolve()
            linked.setdefault(str(cref_path), []).append(pid)

    refs: list[dict[str, Any]] = []
    for path in sorted(SECRETS_REFS_ROOT.glob("*.yaml")):
        validation = _validate_secret_file(path)
        refs.append(
            {
                "name": path.stem,
                "path": str(path),
                "linked_provider_profiles": linked.get(str(path.resolve()), []),
                "validation": validation,
            }
        )
    return refs


def _cloud_credential_overview() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _secret_ref_list():
        provider = str(item.get("validation", {}).get("provider", "")).strip()
        if provider not in {"google", "azure", "aws"}:
            continue
        validation = item.get("validation", {})
        auth = validation.get("auth", {}) if isinstance(validation.get("auth"), dict) else {}
        runtime_ready = bool(auth.get("runtime_ready", validation.get("valid")))
        tone = (
            "valid"
            if runtime_ready and not auth.get("login_recommended")
            else "warning"
            if runtime_ready
            else "invalid"
        )
        rows.append(
            {
                "ref_name": item.get("name", ""),
                "provider": provider,
                "valid": bool(validation.get("valid")),
                "runtime_ready": runtime_ready,
                "state": str(auth.get("status", "") or ("ready" if runtime_ready else "invalid")),
                "message": str(
                    auth.get("message", "") or "; ".join(validation.get("issues", [])) or "ok"
                ),
                "tone": tone,
                "linked_provider_profiles": item.get("linked_provider_profiles", []),
            }
        )
    rows.sort(key=lambda item: item["provider"])
    return rows


def _dataset_stats(samples: list[Any]) -> dict[str, Any]:
    langs = sorted({str(item.language) for item in samples})
    splits: dict[str, int] = {}
    total_duration = 0.0
    for sample in samples:
        split = str(sample.split)
        splits[split] = splits.get(split, 0) + 1
        total_duration += float(sample.duration_sec)
    return {
        "sample_count": len(samples),
        "languages": langs,
        "splits": splits,
        "duration_sec": total_duration,
    }


def _dataset_entries() -> list[dict[str, Any]]:
    registry = DatasetRegistry(str(DATASET_REGISTRY_PATH))
    entries: list[dict[str, Any]] = []
    for entry in registry.list():
        detail = {
            "dataset_id": entry.dataset_id,
            "manifest_ref": entry.manifest_ref,
            "sample_count": int(entry.sample_count),
            "metadata": entry.metadata,
            "valid": True,
            "error": "",
            "languages": [],
            "splits": {},
            "duration_sec": 0.0,
        }
        try:
            samples = load_manifest(entry.manifest_ref)
            stats = _dataset_stats(samples)
            detail.update(stats)
            detail["sample_count"] = int(stats["sample_count"])
        except Exception as exc:
            detail["valid"] = False
            detail["error"] = str(exc)
        entries.append(detail)
    return entries


def _dataset_detail(dataset_id: str) -> dict[str, Any]:
    did = _clean_name(dataset_id, "dataset_id")
    entries = _dataset_entries()
    for item in entries:
        if item["dataset_id"] != did:
            continue
        preview: list[dict[str, Any]] = []
        if item["valid"]:
            samples = load_manifest(item["manifest_ref"])
            preview = [
                {
                    "sample_id": s.sample_id,
                    "audio_path": s.audio_path,
                    "transcript": s.transcript,
                    "language": s.language,
                    "split": s.split,
                    "duration_sec": s.duration_sec,
                    "tags": s.tags,
                }
                for s in samples[:25]
            ]
        return {**item, "preview": preview}
    raise HTTPException(status_code=404, detail=f"Dataset not found: {did}")


def _project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except Exception:
        return str(path.resolve())


def _ensure_dataset_profile(
    dataset_profile: str, manifest_path: str, default_language: str
) -> tuple[str, str]:
    path, pid = _profile_path("datasets", dataset_profile)
    payload = {
        "profile_id": f"datasets/{pid}",
        "inherits": [],
        "dataset_id": pid,
        "manifest_path": _project_relative(Path(manifest_path)),
        "default_language": default_language,
    }
    _write_yaml(path, payload)
    return pid, str(path)


def _list_benchmark_history(limit: int = 50) -> list[dict[str, Any]]:
    with _BENCHMARK_LOCK:
        job_snapshot = dict(_BENCHMARK_JOBS)
    return list_benchmark_history_helper(
        artifacts_root=ARTIFACTS_ROOT,
        read_json=_read_json,
        benchmark_jobs=job_snapshot,
        limit=limit,
    )


def _run_detail(run_id: str) -> dict[str, Any]:
    with _BENCHMARK_LOCK:
        job_snapshot = dict(_BENCHMARK_JOBS)
    return run_detail_helper(
        run_id,
        artifacts_root=ARTIFACTS_ROOT,
        clean_name=_clean_name,
        read_json=_read_json,
        benchmark_jobs=job_snapshot,
    )


def _metric_preference(metric_name: str) -> str:
    return metric_preference_helper(metric_name)


def _compare_runs(run_ids: list[str], metrics: list[str]) -> dict[str, Any]:
    return compare_runs_helper(
        run_ids,
        metrics,
        detail_loader=_run_detail,
        metric_preference_func=_metric_preference,
    )


def _tail_lines(path: Path, limit: int) -> list[str]:
    return tail_lines_helper(path, limit)


def _detect_severity(line: str) -> str:
    return detect_severity_helper(line)


def _log_files(component: str) -> list[Path]:
    return log_files_helper(LOGS_ROOT, component)


def _collect_logs(component: str, severity: str, limit: int) -> list[dict[str, Any]]:
    return collect_logs_helper(LOGS_ROOT, component, severity, limit)


def _diagnostics_issues() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    runtime = _runtime_status()
    if not runtime.get("available"):
        issues.append(
            {
                "severity": "error",
                "component": "runtime",
                "message": "Runtime status service unavailable",
                "suggestion": "Launch runtime stack (`runtime_minimal.launch.py`) and retry.",
            }
        )

    providers = _provider_profiles_summary()
    for row in providers:
        if row.get("valid"):
            continue
        issues.append(
            {
                "severity": "warning",
                "component": "providers",
                "message": f"Provider profile `{row['provider_profile']}` is invalid: {row['message']}",
                "suggestion": "Open Providers page, fix credentials/settings, then validate profile.",
            }
        )

    secrets = _secret_ref_list()
    for item in secrets:
        validation = item.get("validation", {})
        if validation.get("valid"):
            continue
        issues.append(
            {
                "severity": "warning",
                "component": "secrets",
                "message": f"Secret ref `{item['name']}` has issues: {', '.join(validation.get('issues', []))}",
                "suggestion": "Ensure required env vars/files exist, then validate secret ref again.",
            }
        )

    datasets = _dataset_entries()
    if not datasets:
        issues.append(
            {
                "severity": "info",
                "component": "datasets",
                "message": "No datasets registered",
                "suggestion": "Import or register a dataset to enable benchmark flows.",
            }
        )
    for item in datasets:
        if item.get("valid"):
            continue
        issues.append(
            {
                "severity": "warning",
                "component": "datasets",
                "message": f"Dataset `{item['dataset_id']}` manifest problem: {item.get('error', '')}",
                "suggestion": "Check manifest path and schema, then re-register dataset.",
            }
        )

    history = _list_benchmark_history(limit=20)
    failed = [item for item in history if item.get("state") == "failed"]
    if failed:
        latest = failed[0]
        issues.append(
            {
                "severity": "warning",
                "component": "benchmark",
                "message": f"Latest failed benchmark run: {latest['run_id']}",
                "suggestion": "Open Results and Logs to inspect provider/dataset errors.",
            }
        )

    return issues


def _dashboard_payload() -> dict[str, Any]:
    runtime = _runtime_status()
    runtime_snapshot = ros.runtime_snapshot()
    history = _list_benchmark_history(limit=5)
    providers = _provider_profiles_summary()
    issues = _diagnostics_issues()
    cloud_credentials = _cloud_credential_overview()

    with _BENCHMARK_LOCK:
        active = [
            item for item in _BENCHMARK_JOBS.values() if item.get("state") in {"queued", "running"}
        ]

    return {
        "system": {
            "gateway": "online",
            "runtime": runtime,
            "benchmark_active": bool(active),
            "providers_configured": len([row for row in providers if row.get("valid")]),
            "providers_invalid": len([row for row in providers if not row.get("valid")]),
        },
        "runtime": runtime,
        "runtime_live": {
            "recent_results": _merge_runtime_results(
                runtime_snapshot.get("recent_results", []),
                list(_RUNTIME_RESULTS),
            ),
            "recent_partials": list(runtime_snapshot.get("recent_partials", [])),
            "active_session": dict(runtime_snapshot.get("active_session", {})),
            "session_statuses": list(runtime_snapshot.get("session_statuses", [])),
        },
        "benchmark": {
            "active_runs": active,
            "recent_runs": history,
        },
        "cloud_credentials": cloud_credentials,
        "alerts": issues[:10],
        "quick_actions": [
            {"id": "start_runtime", "label": "Start Runtime", "endpoint": "/api/runtime/start"},
            {"id": "stop_runtime", "label": "Stop Runtime", "endpoint": "/api/runtime/stop"},
            {"id": "open_profiles", "label": "Open Profiles", "endpoint": "/api/profiles"},
            {"id": "run_benchmark", "label": "Run Benchmark", "endpoint": "/api/benchmark/run"},
            {"id": "import_dataset", "label": "Import Dataset", "endpoint": "/api/datasets/import"},
        ],
    }


def _benchmark_worker(run_id: str, req: BenchmarkRunRequest) -> None:
    with _BENCHMARK_LOCK:
        state = _BENCHMARK_JOBS.get(run_id, {})
        state["state"] = "running"
        state["started_at"] = _now_iso()
        _BENCHMARK_JOBS[run_id] = state

    response = ros.run_benchmark(
        req.benchmark_profile,
        req.dataset_profile,
        req.providers,
        scenario=req.scenario,
        provider_overrides=req.provider_overrides,
        benchmark_settings=req.benchmark_settings,
        run_id=run_id,
    )

    with _BENCHMARK_LOCK:
        state = _BENCHMARK_JOBS.get(run_id, {})
        state["completed_at"] = _now_iso()
        state["message"] = response.message
        if response.success:
            state["state"] = "completed"
            payload = dict(response.payload)
            summary_payload = payload.get("summary", {})
            if isinstance(summary_payload, dict):
                summary_artifact_ref = Path(
                    str(summary_payload.get("summary_artifact_ref", "") or "")
                )
                hydrated_summary = _read_json(summary_artifact_ref, {})
                if isinstance(hydrated_summary, dict) and hydrated_summary:
                    payload["summary"] = hydrated_summary
            state["result"] = payload
        else:
            state["state"] = "failed"
            state["result"] = response.payload
        _BENCHMARK_JOBS[run_id] = state


# --- Basic health and dashboard endpoints ---
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": _now_iso()}


@app.get("/")
def index() -> Any:
    index_path = PROJECT_ROOT / "web_ui" / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(index_path, headers=_no_cache_headers())
    return {"message": "ASR Gateway API is running"}


@app.get("/api/system/status")
def system_status() -> dict[str, Any]:
    return _dashboard_payload()


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    return _dashboard_payload()


# --- Runtime endpoints used by Dashboard and Runtime pages ---
@app.get("/api/runtime/status")
def runtime_status() -> dict[str, Any]:
    return _runtime_status()


@app.get("/api/runtime/live")
def runtime_live() -> dict[str, Any]:
    snapshot = ros.runtime_snapshot()
    status = _runtime_status()
    normalized_snapshot = _normalize_runtime_session_snapshot(
        snapshot,
        audio_source=str(status.get("audio_source", "") or ""),
    )
    return {
        "status": status,
        "recent_events": list(_RUNTIME_EVENTS),
        "recent_results": normalized_snapshot["recent_results"],
        "recent_partials": normalized_snapshot["recent_partials"],
        "node_statuses": normalized_snapshot["node_statuses"],
        "session_statuses": normalized_snapshot["session_statuses"],
        "active_session": normalized_snapshot["active_session"],
        "time": _now_iso(),
    }


@app.get("/api/runtime/backends")
def runtime_backends() -> dict[str, Any]:
    res = ros.list_backends()
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.payload


@app.get("/api/runtime/samples")
def runtime_samples() -> dict[str, Any]:
    return _list_runtime_samples()


@app.post("/api/runtime/generate_noise")
def runtime_generate_noise(req: NoiseGenerateRequest) -> dict[str, Any]:
    if not req.snr_levels:
        raise HTTPException(status_code=400, detail="At least one SNR level is required.")

    source = _resolve_runtime_sample_path(req.source_wav, label="source_wav")
    if source.suffix.lower() not in RUNTIME_SAMPLE_SUFFIXES:
        raise HTTPException(status_code=400, detail="Noise generation requires a WAV source file.")
    if not source.exists():
        raise HTTPException(status_code=404, detail=f"Source WAV not found: {req.source_wav}")

    generated: list[dict[str, Any]] = []
    for snr_db in req.snr_levels:
        target = _noise_output_target(source, float(snr_db))
        output_path = Path(
            apply_noise_to_wav(
                source_path=str(source),
                output_path=str(target),
                snr_db=float(snr_db),
                seed=1337,
            )
        )
        generated.append(
            {
                "path": _project_relative_path(output_path),
                "snr_db": float(snr_db),
                "name": output_path.name,
                **_wav_metadata_from_file(output_path),
            }
        )

    return {
        "source_wav": _project_relative_path(source),
        "generated": generated,
        "catalog": _list_runtime_samples(),
    }


if MULTIPART_AVAILABLE:

    @app.post("/api/runtime/upload_sample")
    async def runtime_upload_sample(file: UploadFile = File(...)) -> dict[str, Any]:
        upload_name = str(file.filename or "").strip() or "runtime_sample.wav"
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded runtime sample is empty.")

        try:
            metadata = _wav_metadata_from_bytes(content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        target_path = _runtime_upload_target(upload_name)
        target_path.write_bytes(content)
        catalog = _list_runtime_samples()
        return {
            "saved": True,
            "sample_path": _project_relative_path(target_path),
            "sample": {
                "path": _project_relative_path(target_path),
                "name": target_path.name,
                "uploaded": True,
                "size_bytes": len(content),
                **metadata,
            },
            "catalog": catalog,
        }

else:

    @app.post("/api/runtime/upload_sample")
    async def runtime_upload_sample() -> dict[str, Any]:
        raise HTTPException(
            status_code=503,
            detail='Runtime sample upload requires "python-multipart". Install dependencies from requirements.txt.',
        )


@app.post("/api/runtime/start")
def runtime_start(req: RuntimeStartRequest) -> dict[str, Any]:
    preflight = _preflight_runtime_request(
        runtime_profile=req.runtime_profile,
        provider_profile=req.provider_profile,
        provider_preset=req.provider_preset,
        provider_settings=req.provider_settings,
        processing_mode=req.processing_mode,
        audio_source=req.audio_source,
        audio_file_path=req.audio_file_path,
        language=req.language,
        mic_capture_sec=req.mic_capture_sec,
    )
    provider_exec = preflight["provider_exec"]
    res = ros.start_runtime(
        preflight["runtime_profile"],
        provider_exec["normalized_profile"],
        req.session_id,
        processing_mode=preflight["processing_mode"],
        provider_preset=str(provider_exec["execution"].get("selected_preset", "") or ""),
        provider_settings=dict(req.provider_settings or {}),
        audio_source=preflight["audio_source"],
        audio_file_path=preflight["audio_file_path"],
        language=preflight["language"],
        mic_capture_sec=preflight["mic_capture_sec"],
    )
    _record_runtime_event(
        "runtime_start",
        res.message,
        {
            "runtime_profile": preflight["runtime_profile"],
            "provider_profile": provider_exec["normalized_profile"],
            "processing_mode": preflight["processing_mode"],
            "provider_preset": provider_exec["execution"].get("selected_preset", ""),
            "provider_settings": req.provider_settings,
            "session_id": res.payload.get("session_id", req.session_id),
            "audio_source": preflight["audio_source"],
            "audio_file_path": preflight["audio_file_path"]
            if preflight["audio_source"] == "file"
            else "",
            "language": preflight["language"],
            "success": res.success,
            "resolved_config_ref": preflight["resolved_config_ref"],
        },
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


@app.post("/api/runtime/stop")
def runtime_stop(req: RuntimeStopRequest) -> dict[str, Any]:
    res = ros.stop_runtime(req.session_id)
    _record_runtime_event(
        "runtime_stop",
        res.message,
        {"session_id": req.session_id, "success": res.success},
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message}


@app.post("/api/runtime/reconfigure")
def runtime_reconfigure(req: RuntimeReconfigureRequest) -> dict[str, Any]:
    preflight = _preflight_runtime_request(
        runtime_profile=req.runtime_profile,
        provider_profile=req.provider_profile,
        provider_preset=req.provider_preset,
        provider_settings=req.provider_settings,
        processing_mode=req.processing_mode,
        audio_source=req.audio_source,
        audio_file_path=req.audio_file_path,
        language=req.language,
        mic_capture_sec=req.mic_capture_sec,
    )
    provider_exec = preflight["provider_exec"]
    res = ros.reconfigure_runtime(
        req.session_id,
        preflight["runtime_profile"],
        provider_exec["normalized_profile"],
        processing_mode=preflight["processing_mode"],
        provider_preset=str(provider_exec["execution"].get("selected_preset", "") or ""),
        provider_settings=dict(req.provider_settings or {}),
        audio_source=preflight["audio_source"],
        audio_file_path=preflight["audio_file_path"],
        language=preflight["language"],
        mic_capture_sec=preflight["mic_capture_sec"],
    )
    _record_runtime_event(
        "runtime_reconfigure",
        res.message,
        {
            "session_id": req.session_id,
            "runtime_profile": preflight["runtime_profile"],
            "provider_profile": provider_exec["normalized_profile"],
            "processing_mode": preflight["processing_mode"],
            "provider_preset": provider_exec["execution"].get("selected_preset", ""),
            "provider_settings": req.provider_settings,
            "audio_source": preflight["audio_source"],
            "audio_file_path": preflight["audio_file_path"]
            if preflight["audio_source"] == "file"
            else "",
            "language": preflight["language"],
            "success": res.success,
            "resolved_config_ref": preflight["resolved_config_ref"],
        },
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


@app.post("/api/runtime/recognize_once")
def runtime_recognize_once(req: RecognizeRequest) -> dict[str, Any]:
    try:
        provider_exec = _preflight_provider_profile(
            req.provider_profile,
            preset_id=req.provider_preset,
            settings_overrides=req.provider_settings,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    wav_path = _resolve_runtime_sample_path(req.wav_path, label="wav_path")
    if not wav_path.exists():
        raise HTTPException(status_code=404, detail=f"Runtime WAV not found: {req.wav_path}")
    res = ros.recognize_once(
        _project_relative_path(wav_path),
        req.language,
        req.session_id,
        provider_exec["normalized_profile"],
        provider_preset=str(provider_exec["execution"].get("selected_preset", "") or ""),
        provider_settings=dict(req.provider_settings or {}),
    )
    payload = {"message": res.message, **res.payload}
    ros.record_runtime_result(payload)
    _RUNTIME_RESULTS.appendleft({"time": _now_iso(), **payload})
    _record_runtime_event(
        "recognize_once",
        res.message,
        {
            "wav_path": _project_relative_path(wav_path),
            "language": req.language,
            "session_id": req.session_id,
            "provider_profile": provider_exec["normalized_profile"],
            "provider_preset": provider_exec["execution"].get("selected_preset", ""),
            "success": res.success,
        },
    )
    if not res.success and not res.payload:
        raise HTTPException(status_code=400, detail=res.message)
    return payload


# --- Provider inspection and validation endpoints ---
@app.get("/api/providers/catalog")
def providers_catalog() -> dict[str, Any]:
    return {"providers": _provider_catalog()}


@app.get("/api/providers/profiles")
def providers_profiles() -> dict[str, Any]:
    return {"profiles": _provider_profiles_summary()}


@app.post("/api/providers/validate")
def providers_validate(req: ProviderProfileRequest) -> dict[str, Any]:
    manager = ProviderManager(configs_root=str(CONFIGS_ROOT))
    profile = req.provider_profile
    if not profile.startswith("providers/"):
        profile = f"providers/{profile}"

    try:
        provider_exec = _preflight_provider_profile(
            profile,
            preset_id=req.provider_preset,
            settings_overrides=req.provider_settings,
        )
        adapter = manager.create_from_profile(
            provider_exec["normalized_profile"],
            preset_id=str(provider_exec["execution"].get("selected_preset", "") or ""),
            settings_overrides=dict(req.provider_settings or {}),
        )
        caps = _capabilities_to_dict(adapter.discover_capabilities())
        status = adapter.get_status()
        adapter.teardown()
        return {
            "valid": True,
            "message": "Provider profile is valid",
            "provider_profile": provider_exec["normalized_profile"],
            "provider_preset": provider_exec["execution"].get("selected_preset", ""),
            "provider_id": adapter.provider_id,
            "status": status.state,
            "capabilities": caps,
        }
    except Exception as exc:
        return {
            "valid": False,
            "message": str(exc),
            "provider_profile": profile,
        }


@app.post("/api/providers/test")
def providers_test(req: ProviderTestRequest) -> dict[str, Any]:
    manager = ProviderManager(configs_root=str(CONFIGS_ROOT))
    profile = req.provider_profile
    if not profile.startswith("providers/"):
        profile = f"providers/{profile}"
    wav = Path(req.wav_path)
    if not wav.exists():
        raise HTTPException(status_code=400, detail=f"WAV file not found: {wav}")

    try:
        provider_exec = _preflight_provider_profile(
            profile,
            preset_id=req.provider_preset,
            settings_overrides=req.provider_settings,
        )
        adapter = manager.create_from_profile(
            provider_exec["normalized_profile"],
            preset_id=str(provider_exec["execution"].get("selected_preset", "") or ""),
            settings_overrides=dict(req.provider_settings or {}),
        )
        result = adapter.recognize_once(
            ProviderAudio(
                session_id=make_session_id(),
                request_id=make_request_id(),
                language=req.language,
                sample_rate_hz=16000,
                wav_path=str(wav),
                enable_word_timestamps=True,
            )
        )
        adapter.teardown()
        return {
            "success": not result.degraded and not result.error_code,
            "provider_profile": provider_exec["normalized_profile"],
            "provider_preset": provider_exec["execution"].get("selected_preset", ""),
            "provider_id": result.provider_id,
            "text": result.text,
            "latency_ms": result.latency.total_ms,
            "error_code": result.error_code,
            "error_message": result.error_message,
            "confidence": result.confidence,
            "timestamps_available": result.timestamps_available,
            "confidence_available": result.confidence_available,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- Profile CRUD / validation endpoints ---
@app.get("/api/profiles")
def profiles_all() -> dict[str, Any]:
    grouped = {
        profile_type: list_profiles(profile_type, configs_root=str(CONFIGS_ROOT))
        for profile_type in PROFILE_TYPE_DIRS
    }
    return {
        "profiles": grouped,
        "counts": {key: len(value) for key, value in grouped.items()},
    }


@app.get("/api/profiles/{profile_type}")
def profiles(profile_type: str, detailed: bool = Query(False)) -> dict[str, Any]:
    ptype = _normalize_profile_type(profile_type)
    ids = list_profiles(ptype, configs_root=str(CONFIGS_ROOT))
    if not detailed:
        return {"profile_type": ptype, "profiles": ids}
    return {
        "profile_type": ptype,
        "profiles": ids,
        "summaries": _profile_summaries(ptype),
    }


@app.get("/api/profiles/{profile_type}/{profile_id:path}")
def profile_detail(profile_type: str, profile_id: str) -> dict[str, Any]:
    path, pid = _profile_path(profile_type, profile_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_type}/{pid}")
    payload = _read_yaml(path)
    valid, message = _validate_profile(profile_type, pid)
    return {
        "profile_type": _normalize_profile_type(profile_type),
        "profile_id": pid,
        "path": str(path),
        "last_modified": _profile_mtime(path),
        "valid": valid,
        "validation_message": message,
        "links": _profile_links(_normalize_profile_type(profile_type), payload),
        "payload": payload,
    }


@app.put("/api/profiles/{profile_type}/{profile_id:path}")
def profile_save(profile_type: str, profile_id: str, req: ProfileSaveRequest) -> dict[str, Any]:
    path, pid = _profile_path(profile_type, profile_id)
    existing = _read_yaml(path) if path.exists() else {}
    payload = req.payload if req.replace else _deep_merge(existing, req.payload)
    _write_yaml(path, payload)

    valid, message = _validate_profile(profile_type, pid)
    return {
        "saved": True,
        "profile_type": _normalize_profile_type(profile_type),
        "profile_id": pid,
        "path": str(path),
        "valid": valid,
        "validation_message": message,
    }


@app.post("/api/config/validate")
def config_validate(req: ConfigValidateRequest) -> dict[str, Any]:
    res = ros.validate_config(req.profile_type, req.profile_id)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


# --- Secrets and cloud credential management endpoints ---
@app.get("/api/secrets/refs")
def secret_refs() -> dict[str, Any]:
    return {"refs": _secret_ref_list()}


@app.post("/api/secrets/refs")
def secret_refs_upsert(req: SecretRefUpsertRequest) -> dict[str, Any]:
    if req.kind not in {"none", "env", "file"}:
        raise HTTPException(status_code=400, detail=f"Unsupported secret kind: {req.kind}")

    name = _normalize_ref_name(req.file_name)
    path = _secret_ref_path(name)

    payload = {
        "ref_id": req.ref_id,
        "provider": req.provider,
        "kind": req.kind,
        "path": req.path,
        "env_fallback": req.env_fallback,
        "required": req.required,
        "optional": req.optional,
        "masked": bool(req.masked),
    }
    _write_yaml(path, payload)
    return {
        "saved": True,
        "name": name,
        "path": str(path),
        "validation": _validate_secret_file(path),
    }


@app.post("/api/secrets/validate")
def secret_validate(req: SecretValidateRequest) -> dict[str, Any]:
    path = _secret_ref_path(req.ref_name)
    return {
        "name": _normalize_ref_name(req.ref_name),
        "path": str(path),
        "validation": _validate_secret_file(path),
    }


@app.get("/api/secrets/azure_env")
def secret_azure_env() -> dict[str, Any]:
    ref_path = _secret_ref_path("azure_speech_key")
    validation = _validate_secret_file(ref_path)
    auth = validation.get("auth", {}) if isinstance(validation.get("auth"), dict) else {}
    return {
        "ref_name": "azure_speech_key",
        "validation": validation,
        "auth": auth,
    }


@app.get("/api/secrets/google_service_account")
def secret_google_service_account() -> dict[str, Any]:
    ref_path = _secret_ref_path("google_service_account")
    validation = _validate_secret_file(ref_path)
    auth = validation.get("auth", {}) if isinstance(validation.get("auth"), dict) else {}
    return {
        "ref_name": "google_service_account",
        "validation": validation,
        "auth": auth,
    }


if MULTIPART_AVAILABLE:

    @app.post("/api/secrets/google_service_account/upload")
    async def secret_google_service_account_upload(
        file: UploadFile = File(...),
        ref_name: str = Form("google_service_account"),
    ) -> dict[str, Any]:
        normalized_ref = _normalize_ref_name(ref_name)
        ref_path = _secret_ref_path(normalized_ref)
        if not ref_path.exists():
            raise HTTPException(status_code=404, detail=f"Secret ref not found: {normalized_ref}")

        validation = _validate_secret_file(ref_path)
        if validation.get("provider") != "google" or validation.get("kind") != "file":
            raise HTTPException(
                status_code=400,
                detail=f"Secret ref `{normalized_ref}` is not a Google file-based auth ref.",
            )

        upload_name = str(file.filename or "").strip() or "service-account.json"
        if not upload_name.lower().endswith(".json"):
            raise HTTPException(
                status_code=400, detail="Google service-account upload must be a JSON file."
            )

        content = await file.read()
        try:
            parsed = json.loads(content.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Uploaded Google credential file is not valid JSON: {exc}"
            ) from exc

        if not isinstance(parsed, dict) or str(parsed.get("type", "") or "") != "service_account":
            raise HTTPException(
                status_code=400,
                detail="Uploaded Google credential file must be a service-account JSON.",
            )

        target_path = PROJECT_ROOT / "secrets" / "google" / "service-account.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(parsed, ensure_ascii=True, indent=2), encoding="utf-8")
        refreshed = _validate_secret_file(ref_path)
        return {
            "saved": True,
            "ref_name": normalized_ref,
            "target_path": str(target_path),
            "validation": refreshed,
        }


@app.post("/api/secrets/google_service_account/clear")
def secret_google_service_account_clear(req: SecretFileClearRequest) -> dict[str, Any]:
    ref_name = _normalize_ref_name(req.ref_name)
    ref_path = _secret_ref_path(ref_name)
    if not ref_path.exists():
        raise HTTPException(status_code=404, detail=f"Secret ref not found: {ref_name}")

    target_path = PROJECT_ROOT / "secrets" / "google" / "service-account.json"
    if target_path.exists():
        target_path.unlink()
    refreshed = _validate_secret_file(ref_path)
    return {
        "cleared": True,
        "ref_name": ref_name,
        "target_path": str(target_path),
        "validation": refreshed,
    }


@app.post("/api/secrets/azure_env")
def secret_azure_env_save(req: AzureEnvSaveRequest) -> dict[str, Any]:
    ref_name = _normalize_ref_name(req.ref_name)
    ref_path = _secret_ref_path(ref_name)
    if not ref_path.exists():
        raise HTTPException(status_code=404, detail=f"Secret ref not found: {ref_name}")

    validation = _validate_secret_file(ref_path)
    if validation.get("provider") != "azure" or validation.get("kind") != "env":
        raise HTTPException(
            status_code=400,
            detail=f"Secret ref `{ref_name}` is not an Azure env-based auth ref.",
        )

    updates: dict[str, str] = {}
    unset: list[str] = []
    if req.clear_speech_key:
        unset.append("AZURE_SPEECH_KEY")
    elif req.speech_key:
        updates["AZURE_SPEECH_KEY"] = req.speech_key.strip()

    if req.clear_region:
        unset.append("AZURE_SPEECH_REGION")
    elif req.region:
        updates["AZURE_SPEECH_REGION"] = req.region.strip()

    if req.clear_endpoint:
        unset.append("ASR_AZURE_ENDPOINT")
    elif req.endpoint:
        updates["ASR_AZURE_ENDPOINT"] = req.endpoint.strip()

    env_path = write_local_env_values(updates, source_path=str(ref_path), unset=unset)
    refreshed = _validate_secret_file(ref_path)
    return {
        "saved": True,
        "ref_name": ref_name,
        "env_file": str(env_path),
        "validation": refreshed,
    }


@app.post("/api/secrets/aws_sso_login")
def secret_aws_sso_login(req: AwsSsoLoginStartRequest) -> dict[str, Any]:
    ref_name = _normalize_ref_name(req.ref_name)
    path = _secret_ref_path(ref_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Secret ref not found: {ref_name}")

    validation = _validate_secret_file(path)
    if validation.get("provider") != "aws" or validation.get("kind") != "env":
        raise HTTPException(
            status_code=400,
            detail=f"Secret ref `{ref_name}` is not an AWS env-based auth ref.",
        )

    auth = validation.get("auth", {}) if isinstance(validation.get("auth"), dict) else {}
    profile = str(req.profile or auth.get("profile") or os.getenv("AWS_PROFILE", "")).strip()
    if not profile:
        raise HTTPException(
            status_code=400,
            detail="AWS profile is not configured. Set AWS_PROFILE or provide profile in the login request.",
        )
    if auth and not bool(auth.get("uses_sso")):
        raise HTTPException(
            status_code=400,
            detail=(
                f"AWS profile `{profile}` is not configured for IAM Identity Center / SSO login. "
                "Use native access keys or a shared config profile instead."
            ),
        )

    job = _start_aws_login_job(
        ref_name=ref_name,
        profile=profile,
        use_device_code=bool(req.use_device_code),
        no_browser=bool(req.no_browser),
    )
    job_id = str(job.get("job_id", "") or "")
    sso_start_url = str(auth.get("sso_start_url", "") or "")
    if job_id:
        job_stored = False
        with _SECRET_LOGIN_LOCK:
            if job_id in _SECRET_LOGIN_JOBS:
                _SECRET_LOGIN_JOBS[job_id]["sso_start_url"] = sso_start_url
                job_stored = True
        if job_stored:
            job = _aws_login_job_snapshot(job_id)
        else:
            hints = _extract_aws_login_job_hints(
                list(job.get("lines", [])) if isinstance(job.get("lines", []), list) else [],
                start_url=sso_start_url,
            )
            job = {
                **job,
                **hints,
            }
    return {
        "job": job,
        "validation": validation,
    }


@app.get("/api/secrets/aws_sso_login/{job_id}")
def secret_aws_sso_login_status(job_id: str) -> dict[str, Any]:
    return {"job": _aws_login_job_snapshot(job_id)}


@app.post("/api/secrets/aws_sso_login/{job_id}/cancel")
def secret_aws_sso_login_cancel(job_id: str) -> dict[str, Any]:
    with _SECRET_LOGIN_LOCK:
        job = _SECRET_LOGIN_JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"AWS login job not found: {job_id}")
        process = job.get("_process")
        if job.get("state") != "running" or process is None:
            pass
        else:
            if process.poll() is None:
                process.terminate()
            job["state"] = "cancelled"
            job["completed_at"] = _now_iso()
            lines = list(job.get("lines", []))
            if not lines or lines[-1] != "AWS SSO login cancelled from GUI.":
                lines.append("AWS SSO login cancelled from GUI.")
            job["lines"] = lines[-200:]
    return {"job": _aws_login_job_snapshot(job_id)}


@app.post("/api/secrets/link_provider")
def secret_link_provider(req: SecretLinkProviderRequest) -> dict[str, Any]:
    profile_path, pid = _profile_path("providers", req.provider_profile)
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail=f"Provider profile not found: {pid}")

    payload = _read_yaml(profile_path)
    ref_path = _secret_ref_path(req.ref_name)
    if not ref_path.exists():
        raise HTTPException(status_code=404, detail=f"Secret ref not found: {req.ref_name}")

    payload["credentials_ref"] = str(ref_path)
    _write_yaml(profile_path, payload)

    return {
        "linked": True,
        "provider_profile": pid,
        "credentials_ref": str(ref_path),
    }


# --- Dataset registry/import endpoints ---
@app.post("/api/datasets/register")
def datasets_register(req: DatasetRegisterRequest) -> dict[str, Any]:
    res = ros.register_dataset(req.manifest_path, req.dataset_id, req.dataset_profile)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


@app.post("/api/datasets/import")
def datasets_import(req: DatasetImportRequest) -> dict[str, Any]:
    res = ros.import_dataset(
        source_path=req.source_path,
        dataset_id=req.dataset_id,
        dataset_profile=req.dataset_profile,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


if MULTIPART_AVAILABLE:

    @app.post("/api/datasets/import_upload")
    async def datasets_import_upload(
        dataset_id: str = Form(...),
        dataset_profile: str = Form(""),
        language: str = Form("en-US"),
        files: list[UploadFile] = File(...),
    ) -> dict[str, Any]:
        did = _clean_name(dataset_id, "dataset_id")
        profile_id = _normalize_profile_id("datasets", dataset_profile or did)
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")

        uploaded: list[dict[str, Any]] = []
        for item in files:
            filename = str(item.filename or "").strip()
            if not filename:
                continue
            content = await item.read()
            uploaded.append({"name": filename, "content": content})
        if not uploaded:
            raise HTTPException(status_code=400, detail="Uploaded file set is empty")

        try:
            manifest_path, sample_count = import_from_uploaded_files(
                files=uploaded,
                target_dataset_id=did,
                language=language or "en-US",
                imported_root=str(PROJECT_ROOT / "datasets" / "imported"),
                manifests_root=str(PROJECT_ROOT / "datasets" / "manifests"),
            )
            resolved_profile_id, profile_path = _ensure_dataset_profile(
                profile_id, manifest_path, language or "en-US"
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        registry = DatasetRegistry(str(DATASET_REGISTRY_PATH))
        registry.register(
            DatasetEntry(
                dataset_id=did,
                manifest_ref=str(Path(manifest_path).resolve()),
                sample_count=int(sample_count),
                metadata={"dataset_profile": f"datasets/{resolved_profile_id}", "source": "upload"},
            )
        )
        return {
            "success": True,
            "message": "Uploaded dataset imported",
            "dataset_id": did,
            "dataset_profile": f"datasets/{resolved_profile_id}",
            "manifest_path": manifest_path,
            "profile_path": profile_path,
            "sample_count": int(sample_count),
        }

else:

    @app.post("/api/datasets/import_upload")
    async def datasets_import_upload() -> dict[str, Any]:
        raise HTTPException(
            status_code=503,
            detail='Dataset upload requires "python-multipart". Install dependencies from requirements.txt.',
        )


@app.post("/api/datasets/validate_manifest")
def datasets_validate_manifest(req: DatasetValidateManifestRequest) -> dict[str, Any]:
    path = Path(req.manifest_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Manifest not found: {path}")

    samples = load_manifest(str(path))
    missing_audio: list[str] = []
    if req.check_audio_files:
        for sample in samples:
            audio = Path(sample.audio_path)
            if not audio.exists():
                missing_audio.append(sample.audio_path)

    return {
        "valid": not missing_audio,
        "manifest_path": str(path),
        "sample_count": len(samples),
        "missing_audio": missing_audio[:100],
        "languages": sorted({s.language for s in samples}),
        "splits": _dataset_stats(samples)["splits"],
    }


@app.get("/api/datasets")
def datasets_list() -> dict[str, Any]:
    entries = _dataset_entries()
    return {
        "datasets": entries,
        "dataset_ids": [item["dataset_id"] for item in entries],
        "manifest_refs": [item["manifest_ref"] for item in entries],
    }


@app.get("/api/datasets/{dataset_id}")
def datasets_detail(dataset_id: str) -> dict[str, Any]:
    return _dataset_detail(dataset_id)


# --- Benchmark execution endpoints ---
@app.post("/api/benchmark/run")
def benchmark_run(req: BenchmarkRunRequest) -> dict[str, Any]:
    preflight = _preflight_benchmark_request(req)
    run_id = req.run_id.strip() or make_run_id("bench")

    with _BENCHMARK_LOCK:
        if run_id in _BENCHMARK_JOBS and _BENCHMARK_JOBS[run_id].get("state") in {
            "queued",
            "running",
        }:
            raise HTTPException(status_code=400, detail=f"Run is already active: {run_id}")
        _BENCHMARK_JOBS[run_id] = {
            "run_id": run_id,
            "state": "queued",
            "created_at": _now_iso(),
            "benchmark_profile": preflight["benchmark_profile"],
            "dataset_profile": preflight["dataset_profile"],
            "providers": preflight["providers"],
            "scenario": preflight["scenario"],
            "execution_mode": str(
                preflight["benchmark_settings"].get("execution_mode", "batch") or "batch"
            ),
            "message": "Queued",
        }

    worker_req = BenchmarkRunRequest(
        benchmark_profile=preflight["benchmark_profile"],
        dataset_profile=preflight["dataset_profile"],
        providers=preflight["providers"],
        scenario=preflight["scenario"],
        provider_overrides=preflight["provider_overrides"],
        benchmark_settings=preflight["benchmark_settings"],
        run_id=run_id,
    )
    thread = threading.Thread(target=_benchmark_worker, args=(run_id, worker_req), daemon=True)
    thread.start()

    return {
        "accepted": True,
        "run_id": run_id,
        "message": "Benchmark run queued",
    }


@app.get("/api/benchmark/status/{run_id}")
def benchmark_status(run_id: str) -> dict[str, Any]:
    rid = _clean_name(run_id, "run_id")
    with _BENCHMARK_LOCK:
        job = dict(_BENCHMARK_JOBS.get(rid, {}))

    ros_status = ros.get_benchmark_status(rid)
    ros_payload = ros_status.payload if ros_status.success else {}

    if job:
        return {
            "run_id": rid,
            "state": job.get("state", "unknown"),
            "message": job.get("message", ""),
            "created_at": job.get("created_at", ""),
            "started_at": job.get("started_at", ""),
            "completed_at": job.get("completed_at", ""),
            "result": job.get("result", {}),
            "ros_status": ros_payload,
        }

    if ros_status.success:
        return {"run_id": rid, **ros_payload}

    run_dir = _run_dir(rid)
    if run_dir.exists():
        detail = _run_detail(rid)
        return {
            "run_id": rid,
            "state": "completed",
            "message": "Loaded from artifacts",
            "result": detail.get("summary", {}),
        }

    raise HTTPException(status_code=404, detail=f"Run status not found: {rid}")


@app.get("/api/benchmark/history")
def benchmark_history(limit: int = Query(default=30, ge=1, le=200)) -> dict[str, Any]:
    return {"runs": _list_benchmark_history(limit=limit)}


# --- Result browsing/export endpoints ---
@app.get("/api/results/overview")
def results_overview() -> dict[str, Any]:
    history = _list_benchmark_history(limit=20)
    completed = [row for row in history if row.get("state") == "completed"]
    latest = completed[0] if completed else {}
    return {
        "latest_completed": latest,
        "recent_runs": history,
        "comparison_ready_runs": [row["run_id"] for row in completed[:10]],
    }


@app.get("/api/results/runs/{run_id}")
def results_run_detail(run_id: str) -> dict[str, Any]:
    return _run_detail(run_id)


@app.post("/api/results/compare")
def results_compare(req: ResultCompareRequest) -> dict[str, Any]:
    run_ids = [_clean_name(run_id, "run_id") for run_id in req.run_ids]
    return _compare_runs(run_ids, req.metrics)


@app.post("/api/results/export")
def results_export(req: ResultExportRequest) -> dict[str, Any]:
    run_ids = [_clean_name(run_id, "run_id") for run_id in req.run_ids]
    compare_payload = _compare_runs(run_ids, [])

    export_name = (
        req.name.strip() or f"comparison_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    export_name = _clean_name(export_name, "name")
    export_dir = ARTIFACTS_ROOT / "exports" / export_name
    export_dir.mkdir(parents=True, exist_ok=True)

    formats = {item.lower() for item in req.formats}
    outputs: dict[str, str] = {}

    if "json" in formats:
        outputs["json"] = export_json(str(export_dir / "comparison.json"), compare_payload)

    if "csv" in formats:
        rows: list[dict[str, Any]] = []
        for subject in compare_payload.get("subjects", []):
            if not isinstance(subject, dict):
                continue
            entity_id = str(subject.get("entity_id", "") or "")
            row: dict[str, Any] = {
                "entity_id": entity_id,
                "run_id": str(subject.get("run_id", "") or ""),
                "provider_profile": str(subject.get("provider_profile", "") or ""),
                "provider_id": str(subject.get("provider_id", "") or ""),
                "provider_preset": str(subject.get("provider_preset", "") or ""),
            }
            row.update(compare_payload.get("by_run", {}).get(entity_id, {}))
            rows.append(row)
        outputs["csv"] = export_csv(str(export_dir / "comparison.csv"), rows)

    if "md" in formats or "markdown" in formats:
        bullets = [f"Runs: {', '.join(compare_payload.get('run_ids', []))}"]
        for item in compare_payload.get("table", []):
            metric = item.get("metric", "")
            best = item.get("best_run", "")
            bullets.append(f"{metric}: best={best}")
        for run_id, provider_summaries in sorted(
            (compare_payload.get("provider_summaries_by_run", {}) or {}).items()
        ):
            if not provider_summaries:
                continue
            provider_names = ", ".join(
                str(
                    item.get("provider_profile")
                    or item.get("provider_id")
                    or item.get("provider_key")
                    or "unknown"
                )
                for item in provider_summaries
                if isinstance(item, dict)
            )
            bullets.append(f"{run_id} providers: {provider_names}")
        outputs["md"] = export_markdown(
            str(export_dir / "comparison.md"),
            title=f"Run Comparison: {export_name}",
            bullet_items=bullets,
        )

    return {
        "name": export_name,
        "directory": str(export_dir),
        "outputs": outputs,
    }


# --- Diagnostics, logs, and artifact discovery endpoints ---
@app.get("/api/diagnostics/health")
def diagnostics_health() -> dict[str, Any]:
    runtime = _runtime_status()
    providers = _provider_profiles_summary()
    datasets = _dataset_entries()
    history = _list_benchmark_history(limit=10)

    return {
        "runtime": {
            "available": runtime.get("available", False),
            "state": runtime.get("state", "unknown"),
            "backend": runtime.get("backend", ""),
            "session_id": runtime.get("session_id", ""),
        },
        "providers": {
            "total_profiles": len(providers),
            "valid_profiles": len([row for row in providers if row.get("valid")]),
            "invalid_profiles": len([row for row in providers if not row.get("valid")]),
        },
        "datasets": {
            "registered": len(datasets),
            "valid": len([row for row in datasets if row.get("valid")]),
            "invalid": len([row for row in datasets if not row.get("valid")]),
        },
        "benchmark": {
            "recent_runs": history[:5],
            "active_runs": [row for row in history if row.get("state") in {"queued", "running"}],
        },
    }


@app.get("/api/diagnostics/preflight")
def diagnostics_preflight() -> dict[str, Any]:
    return _run_preflight_checks()


@app.get("/api/diagnostics/issues")
def diagnostics_issues() -> dict[str, Any]:
    issues = _diagnostics_issues()
    return {
        "issues": issues,
        "counts": {
            "error": len([item for item in issues if item.get("severity") == "error"]),
            "warning": len([item for item in issues if item.get("severity") == "warning"]),
            "info": len([item for item in issues if item.get("severity") == "info"]),
        },
    }


@app.get("/api/logs")
def logs(
    component: str = Query(default="all"),
    severity: str = Query(default="all"),
    limit: int = Query(default=200, ge=1, le=2000),
) -> dict[str, Any]:
    files = [str(path) for path in _log_files(component=component)]
    entries = _collect_logs(component=component, severity=severity, limit=limit)
    return {
        "component": component,
        "severity": severity,
        "limit": limit,
        "files": files,
        "entry_count": len(entries),
        "entries": entries,
    }


@app.get("/api/artifacts")
def artifacts() -> dict[str, Any]:
    root = ARTIFACTS_ROOT
    root.mkdir(parents=True, exist_ok=True)
    benchmark_runs = sorted(
        path.name for path in (root / "benchmark_runs").glob("*") if path.is_dir()
    )
    runtime_sessions = sorted(
        path.name for path in (root / "runtime_sessions").glob("*") if path.is_dir()
    )
    comparisons = sorted(path.name for path in (root / "comparisons").glob("*") if path.is_dir())
    exports = sorted(path.name for path in (root / "exports").glob("*") if path.is_dir())
    return {
        "benchmark_runs": benchmark_runs,
        "runtime_sessions": runtime_sessions,
        "comparisons": comparisons,
        "exports": exports,
    }
