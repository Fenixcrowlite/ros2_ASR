"""Request validation helpers for GUI job launches."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from web_gui.app.paths import REPO_ROOT, resolve_under_roots

_LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?$")


def _as_int(raw: Any, *, fallback: int) -> int:
    if raw is None or raw == "":
        return fallback
    try:
        return int(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid integer value: {raw}") from exc


def _validate_language(payload: dict[str, Any]) -> None:
    mode = str(payload.get("language_mode") or "config").strip().lower()
    language = str(payload.get("language") or "").strip()
    if mode not in {"manual", "auto", "config"}:
        raise HTTPException(status_code=400, detail=f"Invalid language_mode: {mode}")
    if mode == "manual" and language and not _LANGUAGE_RE.match(language):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid language code '{language}'. Use format like en-US, ru-RU, de-DE."
            ),
        )


def _validate_sample_rate(payload: dict[str, Any], runtime_overrides: dict[str, Any]) -> None:
    sample_rate = payload.get("sample_rate")
    if sample_rate in {None, ""}:
        sample_rate = (
            dict(runtime_overrides.get("asr", {})).get("sample_rate")
            if isinstance(runtime_overrides.get("asr", {}), dict)
            else 16000
        )
    rate = _as_int(sample_rate, fallback=16000)
    if rate < 8000 or rate > 48000:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported sample_rate={rate}. Allowed range is 8000..48000.",
        )


def _validate_dataset(payload: dict[str, Any]) -> None:
    dataset = str(payload.get("dataset") or "data/transcripts/sample_manifest.csv")
    try:
        path = resolve_under_roots(
            dataset,
            roots=[REPO_ROOT / "data", REPO_ROOT / "web_gui", REPO_ROOT / "results"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=400, detail=f"Dataset not found: {path}")
    if path.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail=f"Dataset must be CSV: {path}")


def _validate_wav_if_provided(payload: dict[str, Any], *, key: str) -> None:
    raw = str(payload.get(key) or "").strip()
    if not raw:
        return
    try:
        path = resolve_under_roots(
            raw,
            roots=[REPO_ROOT / "data", REPO_ROOT / "web_gui", REPO_ROOT / "results"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=400, detail=f"WAV not found: {path}")
    if path.suffix.lower() != ".wav":
        raise HTTPException(status_code=400, detail=f"File must be WAV: {path}")


def validate_live_request(payload: dict[str, Any], runtime_overrides: dict[str, Any]) -> None:
    """Validate live sample payload before creating job."""
    _validate_language(payload)
    _validate_sample_rate(payload, runtime_overrides)
    _validate_wav_if_provided(payload, key="use_wav")



def validate_benchmark_request(payload: dict[str, Any], runtime_overrides: dict[str, Any]) -> None:
    """Validate benchmark payload before creating job."""
    _validate_dataset(payload)
    _validate_sample_rate(payload, runtime_overrides)



def validate_ros_bringup_request(
    payload: dict[str, Any], runtime_overrides: dict[str, Any]
) -> None:
    """Validate ros bringup payload before creating job."""
    _validate_sample_rate(payload, runtime_overrides)
    _validate_wav_if_provided(payload, key="wav_path")

    input_mode = str(payload.get("input_mode") or "mic").strip().lower()
    if input_mode not in {"mic", "file", "auto"}:
        raise HTTPException(status_code=400, detail=f"Invalid input_mode: {input_mode}")

    if input_mode == "file" and not str(payload.get("wav_path") or "").strip():
        raise HTTPException(status_code=400, detail="wav_path is required when input_mode=file")

    install_setup = REPO_ROOT / "install" / "setup.bash"
    if not install_setup.exists():
        raise HTTPException(
            status_code=400,
            detail="ROS workspace not built yet. Run: make build",
        )

    text_enabled = bool(payload.get("text_output_enabled", True))
    if text_enabled:
        text_exec = REPO_ROOT / "install" / "asr_ros" / "lib" / "asr_ros" / "asr_text_output_node"
        if not text_exec.exists():
            raise HTTPException(
                status_code=400,
                detail=(
                    "asr_text_output_node is not installed in ROS workspace. "
                    "Run: make build"
                ),
            )
