"""Gateway API server bridging GUI and ROS2/core layers."""

from __future__ import annotations

import json
import os
import re
import threading
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from asr_backend_aws.backend import AwsAsrBackend
from asr_config import (
    list_profiles,
    load_secret_ref,
    resolve_profile,
    resolve_secret_ref,
    validate_benchmark_payload,
    validate_runtime_payload,
)
from asr_core import make_request_id, make_run_id, make_session_id
from asr_datasets import DatasetRegistry, load_manifest
from asr_gateway.ros_client import GatewayRosClient
from asr_provider_base import ProviderAudio, ProviderManager, create_provider, list_providers
from asr_reporting import export_csv, export_json, export_markdown
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


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
CONFIGS_ROOT = PROJECT_ROOT / "configs"
SECRETS_REFS_ROOT = PROJECT_ROOT / "secrets" / "refs"
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"
LOGS_ROOT = PROJECT_ROOT / "logs"
DATASET_REGISTRY_PATH = PROJECT_ROOT / "datasets" / "registry" / "datasets.json"

_RUNTIME_EVENTS: deque[dict[str, Any]] = deque(maxlen=200)
_RUNTIME_RESULTS: deque[dict[str, Any]] = deque(maxlen=80)
_BENCHMARK_JOBS: dict[str, dict[str, Any]] = {}
_BENCHMARK_LOCK = threading.Lock()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    del app
    try:
        yield
    finally:
        ros.close()


app = FastAPI(title="ASR Gateway", version="0.2.0", lifespan=_lifespan)
ros = GatewayRosClient(timeout_sec=5.0)
if (PROJECT_ROOT / "web_ui" / "frontend").exists():
    app.mount("/ui", NoCacheStaticFiles(directory=str(PROJECT_ROOT / "web_ui" / "frontend")), name="ui")


class RuntimeStartRequest(BaseModel):
    runtime_profile: str = "default_runtime"
    provider_profile: str = "providers/whisper_local"
    session_id: str = ""
    audio_source: str = "file"
    audio_file_path: str = "data/sample/en_hello.wav"
    language: str = "en-US"
    mic_capture_sec: float = 4.0


class RuntimeStopRequest(BaseModel):
    session_id: str = ""


class RuntimeReconfigureRequest(BaseModel):
    session_id: str = ""
    runtime_profile: str = "default_runtime"
    provider_profile: str = "providers/whisper_local"
    audio_source: str = "file"
    audio_file_path: str = "data/sample/en_hello.wav"
    language: str = "en-US"
    mic_capture_sec: float = 4.0


class RecognizeRequest(BaseModel):
    wav_path: str
    language: str = "en-US"
    session_id: str = ""
    provider_profile: str = ""


class BenchmarkRunRequest(BaseModel):
    benchmark_profile: str = "default_benchmark"
    dataset_profile: str = "sample_dataset"
    providers: list[str] = Field(default_factory=list)
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


class ProviderTestRequest(BaseModel):
    provider_profile: str
    wav_path: str = "data/sample/en_hello.wav"
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
    rid = _clean_name(run_id, "run_id")
    return ARTIFACTS_ROOT / "benchmark_runs" / rid


def _session_dir(session_id: str) -> Path:
    sid = _clean_name(session_id, "session_id")
    return ARTIFACTS_ROOT / "runtime_sessions" / sid


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
            "audio_source": "",
            "runtime_profile": active_session.get("profile_id", ""),
            "observer_error": snapshot.get("observer_error", ""),
        }
    payload = dict(result.payload)
    payload["available"] = True
    payload["state"] = str(payload.get("session_state", payload.get("status_message", "unknown")))
    payload["message"] = "ok"
    payload["observer_error"] = snapshot.get("observer_error", "")
    return payload


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
        resolved = resolve_profile(profile_type=ptype, profile_id=pid, configs_root=str(CONFIGS_ROOT))
        if ptype == "runtime":
            errors = validate_runtime_payload(resolved.data)
            if errors:
                return False, "; ".join(errors)
        if ptype == "benchmark":
            errors = validate_benchmark_payload(resolved.data)
            if errors:
                return False, "; ".join(errors)
        return True, "valid"
    except Exception as exc:
        return False, str(exc)


def _profile_links(profile_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if profile_type == "runtime":
        orchestrator = payload.get("orchestrator", {}) if isinstance(payload.get("orchestrator"), dict) else {}
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
    name = _clean_name(ref_name, "ref_name")
    if name.endswith(".yaml"):
        name = name[:-5]
    return name


def _secret_ref_path(ref_name: str) -> Path:
    return SECRETS_REFS_ROOT / f"{_normalize_ref_name(ref_name)}.yaml"


def _validate_secret_file(path: Path) -> dict[str, Any]:
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
            if ref.env_fallback and os.getenv(ref.env_fallback):
                source = "env_fallback"
        except Exception as exc:
            if str(exc):
                issues.append(str(exc))
        detail["resolved_file_path"] = file_path
        detail["resolved_file_path_source"] = source
        if file_path and not Path(file_path).exists():
            issues.append(f"resolved credential file not found: {file_path}")
        if not file_path:
            issues.append("credential file path is not set")

    for name in ref.required:
        present = bool(os.getenv(name, "").strip())
        detail["env"][name] = {"present": present, "required": True}
        if not present:
            issues.append(f"required env missing: {name}")

    for name in ref.optional:
        present = bool(os.getenv(name, "").strip())
        detail["env"][name] = {"present": present, "required": False}

    if ref.provider == "aws" and ref.kind == "env":
        backend = AwsAsrBackend(
            config={
                "profile": os.getenv("AWS_PROFILE", "").strip(),
                "region": os.getenv("AWS_REGION", "").strip(),
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "").strip(),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "").strip(),
                "session_token": os.getenv("AWS_SESSION_TOKEN", "").strip(),
                "config_file": os.getenv("AWS_CONFIG_FILE", "").strip(),
                "shared_credentials_file": os.getenv("AWS_SHARED_CREDENTIALS_FILE", "").strip(),
            }
        )
        issues.extend(
            issue for issue in backend.auth_validation_errors() if issue and issue not in issues
        )

    detail["valid"] = not issues
    return detail


def _normalize_provider_profile(profile: str) -> str:
    clean = str(profile).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="provider_profile is required")
    return clean if clean.startswith("providers/") else f"providers/{clean}"


def _preflight_provider_profile(profile: str) -> str:
    normalized = _normalize_provider_profile(profile)
    manager = ProviderManager(configs_root=str(CONFIGS_ROOT))
    adapter = manager.create_from_profile(normalized)
    adapter.teardown()
    return normalized


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


def _list_benchmark_history(limit: int = 50) -> list[dict[str, Any]]:
    root = ARTIFACTS_ROOT / "benchmark_runs"
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    run_dirs = [path for path in root.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    with _BENCHMARK_LOCK:
        job_snapshot = dict(_BENCHMARK_JOBS)

    for run_dir in run_dirs[:limit]:
        run_id = run_dir.name
        summary = _read_json(run_dir / "reports" / "summary.json", {})
        run_manifest = _read_json(run_dir / "manifest" / "run_manifest.json", {})
        job = job_snapshot.get(run_id, {})
        state = str(job.get("state", "completed" if summary else "unknown"))

        rows.append(
            {
                "run_id": run_id,
                "state": state,
                "started_at": job.get("started_at", run_manifest.get("created_at", "")),
                "completed_at": job.get("completed_at", ""),
                "benchmark_profile": run_manifest.get("benchmark_profile", ""),
                "dataset_profile": run_manifest.get("dataset_profile", ""),
                "providers": run_manifest.get("providers", []),
                "total_samples": summary.get("total_samples", run_manifest.get("sample_count", 0)),
                "successful_samples": summary.get("successful_samples", 0),
                "failed_samples": summary.get("failed_samples", 0),
                "mean_metrics": summary.get("mean_metrics", {}),
                "run_dir": str(run_dir),
            }
        )

    # include in-memory runs that are not yet materialized on disk
    existing_ids = {row["run_id"] for row in rows}
    for run_id, state in job_snapshot.items():
        if run_id in existing_ids:
            continue
        rows.insert(
            0,
            {
                "run_id": run_id,
                "state": state.get("state", "unknown"),
                "started_at": state.get("started_at", ""),
                "completed_at": state.get("completed_at", ""),
                "benchmark_profile": state.get("benchmark_profile", ""),
                "dataset_profile": state.get("dataset_profile", ""),
                "providers": state.get("providers", []),
                "total_samples": 0,
                "successful_samples": 0,
                "failed_samples": 0,
                "mean_metrics": {},
                "run_dir": "",
            },
        )

    return rows[:limit]


def _run_detail(run_id: str) -> dict[str, Any]:
    run_dir = _run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    run_manifest = _read_json(run_dir / "manifest" / "run_manifest.json", {})
    summary = _read_json(run_dir / "reports" / "summary.json", {})
    metrics_rows = _read_json(run_dir / "metrics" / "results.json", [])

    with _BENCHMARK_LOCK:
        state = _BENCHMARK_JOBS.get(run_id, {}).get("state", "completed")

    return {
        "run_id": run_id,
        "state": state,
        "run_manifest": run_manifest,
        "summary": summary,
        "results_head": metrics_rows[:100],
        "results_count": len(metrics_rows) if isinstance(metrics_rows, list) else 0,
        "artifacts": {
            "manifest": str(run_dir / "manifest" / "run_manifest.json"),
            "summary_json": str(run_dir / "reports" / "summary.json"),
            "summary_md": str(run_dir / "reports" / "summary.md"),
            "results_json": str(run_dir / "metrics" / "results.json"),
            "results_csv": str(run_dir / "metrics" / "results.csv"),
        },
    }


def _metric_preference(metric_name: str) -> str:
    lowered = metric_name.lower()
    if any(token in lowered for token in ("wer", "cer", "latency", "error", "failure", "timeout", "rtf")):
        return "lower"
    return "higher"


def _compare_runs(run_ids: list[str], metrics: list[str]) -> dict[str, Any]:
    if not run_ids:
        raise HTTPException(status_code=400, detail="run_ids must not be empty")

    details = [_run_detail(run_id) for run_id in run_ids]
    summaries = [detail.get("summary", {}) for detail in details]

    metric_names = sorted(
        set(metrics)
        if metrics
        else {
            key
            for summary in summaries
            for key in (summary.get("mean_metrics", {}) or {}).keys()
        }
    )

    by_run: dict[str, dict[str, float]] = {}
    for detail in details:
        run_id = str(detail.get("run_id", ""))
        mean_metrics = detail.get("summary", {}).get("mean_metrics", {})
        row: dict[str, float] = {}
        for metric in metric_names:
            value = mean_metrics.get(metric)
            if value is None:
                continue
            row[metric] = float(value)
        by_run[run_id] = row

    table: list[dict[str, Any]] = []
    for metric in metric_names:
        values = {run_id: by_run.get(run_id, {}).get(metric) for run_id in run_ids}
        available = {run_id: val for run_id, val in values.items() if val is not None}
        best_run = ""
        if available:
            if _metric_preference(metric) == "lower":
                best_run = min(available, key=available.get)
            else:
                best_run = max(available, key=available.get)

        table.append(
            {
                "metric": metric,
                "preference": _metric_preference(metric),
                "values": values,
                "best_run": best_run,
            }
        )

    return {
        "run_ids": run_ids,
        "metrics": metric_names,
        "by_run": by_run,
        "table": table,
    }


def _tail_lines(path: Path, limit: int) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    return content[-limit:]


def _detect_severity(line: str) -> str:
    lowered = line.lower()
    if "error" in lowered:
        return "error"
    if "warn" in lowered:
        return "warning"
    if "debug" in lowered:
        return "debug"
    return "info"


def _log_files(component: str) -> list[Path]:
    mapping = {
        "runtime": LOGS_ROOT / "runtime",
        "benchmark": LOGS_ROOT / "benchmark",
        "gateway": LOGS_ROOT / "gateway",
        "gui": LOGS_ROOT / "gui",
    }
    components = [component] if component != "all" else sorted(mapping.keys())

    files: list[Path] = []
    for comp in components:
        base = mapping.get(comp)
        if base is None or not base.exists():
            continue
        candidates = [path for path in base.rglob("*") if path.is_file()]
        candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        files.extend(candidates[:3])
    return files


def _collect_logs(component: str, severity: str, limit: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    sev = severity.lower()
    for path in _log_files(component):
        try:
            rel = path.relative_to(LOGS_ROOT)
            comp = rel.parts[0] if rel.parts else "unknown"
        except ValueError:
            comp = "unknown"
        for line in _tail_lines(path, limit):
            detected = _detect_severity(line)
            if sev != "all" and detected != sev:
                continue
            output.append(
                {
                    "component": comp,
                    "file": str(path),
                    "severity": detected,
                    "message": line,
                }
            )
    return output[-limit:]


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

    with _BENCHMARK_LOCK:
        active = [item for item in _BENCHMARK_JOBS.values() if item.get("state") in {"queued", "running"}]

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
        run_id=run_id,
    )

    with _BENCHMARK_LOCK:
        state = _BENCHMARK_JOBS.get(run_id, {})
        state["completed_at"] = _now_iso()
        state["message"] = response.message
        if response.success:
            state["state"] = "completed"
            state["result"] = response.payload
        else:
            state["state"] = "failed"
            state["result"] = response.payload
        _BENCHMARK_JOBS[run_id] = state


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


@app.get("/api/runtime/status")
def runtime_status() -> dict[str, Any]:
    return _runtime_status()


@app.get("/api/runtime/live")
def runtime_live() -> dict[str, Any]:
    snapshot = ros.runtime_snapshot()
    return {
        "status": _runtime_status(),
        "recent_events": list(_RUNTIME_EVENTS),
        "recent_results": _merge_runtime_results(snapshot.get("recent_results", []), list(_RUNTIME_RESULTS)),
        "recent_partials": list(snapshot.get("recent_partials", [])),
        "node_statuses": list(snapshot.get("node_statuses", [])),
        "session_statuses": list(snapshot.get("session_statuses", [])),
        "active_session": dict(snapshot.get("active_session", {})),
        "time": _now_iso(),
    }


@app.get("/api/runtime/backends")
def runtime_backends() -> dict[str, Any]:
    res = ros.list_backends()
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.payload


@app.post("/api/runtime/start")
def runtime_start(req: RuntimeStartRequest) -> dict[str, Any]:
    try:
        normalized_provider_profile = _preflight_provider_profile(req.provider_profile)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    res = ros.start_runtime(
        req.runtime_profile,
        normalized_provider_profile,
        req.session_id,
        audio_source=req.audio_source,
        audio_file_path=req.audio_file_path,
        language=req.language,
        mic_capture_sec=req.mic_capture_sec,
    )
    _record_runtime_event(
        "runtime_start",
        res.message,
        {
            "runtime_profile": req.runtime_profile,
            "provider_profile": normalized_provider_profile,
            "session_id": res.payload.get("session_id", req.session_id),
            "audio_source": req.audio_source,
            "audio_file_path": req.audio_file_path if req.audio_source == "file" else "",
            "language": req.language,
            "success": res.success,
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
    try:
        normalized_provider_profile = _preflight_provider_profile(req.provider_profile)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    res = ros.reconfigure_runtime(
        req.session_id,
        req.runtime_profile,
        normalized_provider_profile,
        audio_source=req.audio_source,
        audio_file_path=req.audio_file_path,
        language=req.language,
        mic_capture_sec=req.mic_capture_sec,
    )
    _record_runtime_event(
        "runtime_reconfigure",
        res.message,
        {
            "session_id": req.session_id,
            "runtime_profile": req.runtime_profile,
            "provider_profile": normalized_provider_profile,
            "audio_source": req.audio_source,
            "audio_file_path": req.audio_file_path if req.audio_source == "file" else "",
            "language": req.language,
            "success": res.success,
        },
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"message": res.message, **res.payload}


@app.post("/api/runtime/recognize_once")
def runtime_recognize_once(req: RecognizeRequest) -> dict[str, Any]:
    try:
        normalized_provider_profile = _preflight_provider_profile(req.provider_profile)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    res = ros.recognize_once(req.wav_path, req.language, req.session_id, normalized_provider_profile)
    payload = {"message": res.message, **res.payload}
    ros.record_runtime_result(payload)
    _RUNTIME_RESULTS.appendleft({"time": _now_iso(), **payload})
    _record_runtime_event(
        "recognize_once",
        res.message,
        {
            "wav_path": req.wav_path,
            "language": req.language,
            "session_id": req.session_id,
            "provider_profile": normalized_provider_profile,
            "success": res.success,
        },
    )
    if not res.success and not res.payload:
        raise HTTPException(status_code=400, detail=res.message)
    return payload


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
        adapter = manager.create_from_profile(profile)
        caps = _capabilities_to_dict(adapter.discover_capabilities())
        status = adapter.get_status()
        adapter.teardown()
        return {
            "valid": True,
            "message": "Provider profile is valid",
            "provider_profile": profile,
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
        adapter = manager.create_from_profile(profile)
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
            "provider_profile": profile,
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


@app.post("/api/benchmark/run")
def benchmark_run(req: BenchmarkRunRequest) -> dict[str, Any]:
    run_id = req.run_id.strip() or make_run_id("bench")

    with _BENCHMARK_LOCK:
        if run_id in _BENCHMARK_JOBS and _BENCHMARK_JOBS[run_id].get("state") in {"queued", "running"}:
            raise HTTPException(status_code=400, detail=f"Run is already active: {run_id}")
        _BENCHMARK_JOBS[run_id] = {
            "run_id": run_id,
            "state": "queued",
            "created_at": _now_iso(),
            "benchmark_profile": req.benchmark_profile,
            "dataset_profile": req.dataset_profile,
            "providers": req.providers,
            "message": "Queued",
        }

    worker_req = BenchmarkRunRequest(
        benchmark_profile=req.benchmark_profile,
        dataset_profile=req.dataset_profile,
        providers=req.providers,
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

    export_name = req.name.strip() or f"comparison_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    export_name = _clean_name(export_name, "name")
    export_dir = ARTIFACTS_ROOT / "exports" / export_name
    export_dir.mkdir(parents=True, exist_ok=True)

    formats = {item.lower() for item in req.formats}
    outputs: dict[str, str] = {}

    if "json" in formats:
        outputs["json"] = export_json(str(export_dir / "comparison.json"), compare_payload)

    if "csv" in formats:
        rows: list[dict[str, Any]] = []
        for run_id in compare_payload.get("run_ids", []):
            row: dict[str, Any] = {"run_id": run_id}
            row.update(compare_payload.get("by_run", {}).get(run_id, {}))
            rows.append(row)
        outputs["csv"] = export_csv(str(export_dir / "comparison.csv"), rows)

    if "md" in formats or "markdown" in formats:
        bullets = [f"Runs: {', '.join(compare_payload.get('run_ids', []))}"]
        for item in compare_payload.get("table", []):
            metric = item.get("metric", "")
            best = item.get("best_run", "")
            bullets.append(f"{metric}: best={best}")
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
    entries = _collect_logs(component=component, severity=severity, limit=limit)
    return {
        "component": component,
        "severity": severity,
        "limit": limit,
        "entries": entries,
    }


@app.get("/api/artifacts")
def artifacts() -> dict[str, Any]:
    root = ARTIFACTS_ROOT
    root.mkdir(parents=True, exist_ok=True)
    benchmark_runs = sorted(path.name for path in (root / "benchmark_runs").glob("*") if path.is_dir())
    runtime_sessions = sorted(path.name for path in (root / "runtime_sessions").glob("*") if path.is_dir())
    comparisons = sorted(path.name for path in (root / "comparisons").glob("*") if path.is_dir())
    exports = sorted(path.name for path in (root / "exports").glob("*") if path.is_dir())
    return {
        "benchmark_runs": benchmark_runs,
        "runtime_sessions": runtime_sessions,
        "comparisons": comparisons,
        "exports": exports,
    }
