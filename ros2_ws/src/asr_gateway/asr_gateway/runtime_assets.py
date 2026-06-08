"""Helpers for runtime sample catalog, upload, and noise artifacts."""

from __future__ import annotations

import io
import re
import wave
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

DEFAULT_RUNTIME_SAMPLE = "data/sample/vosk_test.wav"


def wav_metadata_from_bytes(content: bytes) -> dict[str, Any]:
    try:
        with wave.open(io.BytesIO(content), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            sample_rate_hz = wav_file.getframerate()
            duration_sec = frame_count / float(sample_rate_hz) if sample_rate_hz else 0.0
            return {
                "channels": wav_file.getnchannels(),
                "sample_rate_hz": sample_rate_hz,
                "sample_width_bytes": wav_file.getsampwidth(),
                "frame_count": frame_count,
                "duration_sec": round(duration_sec, 3),
            }
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"not a valid WAV file: {exc}") from exc


def wav_metadata_from_file(path: Path) -> dict[str, Any]:
    return wav_metadata_from_bytes(path.read_bytes())


def extract_wav_segment(
    source: Path,
    *,
    output_path: Path,
    start_sec: float = 0.0,
    duration_sec: float | None = None,
) -> dict[str, Any]:
    if start_sec < 0.0:
        raise ValueError("start_sec must be >= 0")
    if duration_sec is not None and duration_sec <= 0.0:
        raise ValueError("duration_sec must be > 0 when provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(source), "rb") as reader:
        frame_rate = int(reader.getframerate() or 0)
        frame_count = int(reader.getnframes() or 0)
        source_duration_sec = frame_count / float(frame_rate) if frame_rate > 0 else 0.0
        if frame_rate <= 0:
            raise ValueError(f"WAV file has invalid frame rate: {source}")
        if start_sec > source_duration_sec:
            raise ValueError(
                f"start_sec exceeds source duration ({source_duration_sec:.3f}s): {start_sec:.3f}s"
            )

        start_frame = min(int(start_sec * frame_rate), frame_count)
        if duration_sec is None:
            frames_to_copy = max(frame_count - start_frame, 0)
        else:
            frames_to_copy = min(
                max(int(duration_sec * frame_rate), 1),
                max(frame_count - start_frame, 0),
            )

        with wave.open(str(output_path), "wb") as writer:
            writer.setparams(reader.getparams())
            if start_frame > 0:
                reader.setpos(start_frame)
            remaining = frames_to_copy
            chunk_frames = max(frame_rate, 1)
            while remaining > 0:
                chunk = reader.readframes(min(chunk_frames, remaining))
                if not chunk:
                    break
                writer.writeframes(chunk)
                bytes_per_frame = max(reader.getnchannels() * reader.getsampwidth(), 1)
                remaining -= len(chunk) // bytes_per_frame

    clip_duration_sec = frames_to_copy / float(frame_rate) if frame_rate > 0 else 0.0
    return {
        "start_sec": float(start_sec),
        "duration_sec": float(clip_duration_sec),
        "source_duration_sec": float(source_duration_sec),
        "output_path": str(output_path),
    }


def list_runtime_samples(
    *,
    samples_root: Path,
    uploads_root: Path,
    project_relative_path: Callable[[Path], str],
    sample_suffixes: set[str],
    upload_enabled: bool,
    default_sample: str = DEFAULT_RUNTIME_SAMPLE,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    if samples_root.exists():
        for path in sorted(item for item in samples_root.rglob("*") if item.is_file()):
            relative_path = project_relative_path(path)
            if path.suffix.lower() not in sample_suffixes:
                skipped.append({"path": relative_path, "reason": "unsupported file extension"})
                continue
            try:
                metadata = wav_metadata_from_file(path)
            except Exception as exc:
                skipped.append({"path": relative_path, "reason": str(exc)})
                continue

            stat_result = path.stat()
            samples.append(
                {
                    "path": relative_path,
                    "name": path.name,
                    "uploaded": "uploads" in path.parts,
                    "size_bytes": stat_result.st_size,
                    "modified_at": datetime.fromtimestamp(stat_result.st_mtime, UTC).isoformat(),
                    **metadata,
                }
            )

    samples.sort(key=lambda item: (bool(item.get("uploaded")), str(item.get("path", ""))))
    sample_paths = [item["path"] for item in samples]
    resolved_default = default_sample
    if resolved_default not in sample_paths:
        preferred = next((item["path"] for item in samples if not item.get("uploaded")), "")
        resolved_default = preferred or (sample_paths[0] if sample_paths else "")

    return {
        "root": project_relative_path(samples_root),
        "upload_root": project_relative_path(uploads_root),
        "default_sample": resolved_default,
        "sample_count": len(samples),
        "samples": samples,
        "skipped": skipped,
        "upload_enabled": upload_enabled,
    }


def runtime_upload_target(
    filename: str,
    *,
    uploads_root: Path,
    sample_suffixes: set[str],
) -> Path:
    base_name = Path(str(filename or "").strip() or "runtime_sample.wav").name
    suffix = Path(base_name).suffix.lower()
    if suffix not in sample_suffixes:
        raise HTTPException(
            status_code=400,
            detail="Runtime sample upload currently supports WAV files only.",
        )

    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(base_name).stem).strip("._")
    stem = stem or "runtime_sample"
    uploads_root.mkdir(parents=True, exist_ok=True)
    target = uploads_root / f"{stem}.wav"
    counter = 1
    while target.exists():
        target = uploads_root / f"{stem}_{counter}.wav"
        counter += 1
    return target


def resolve_runtime_sample_path(
    value: str,
    *,
    clean_name: Callable[[str, str], str],
    project_root: Path,
    allowed_roots: Iterable[Path],
    label: str = "sample_path",
) -> Path:
    raw = str(value or "").strip()
    if not raw:
        clean_name(raw, label)
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        relative = clean_name(raw, label)
        candidate = (project_root / relative).resolve()
    resolved_roots = [root.resolve() for root in allowed_roots]
    if not any(candidate.is_relative_to(root) for root in resolved_roots):
        raise HTTPException(status_code=400, detail=f"Unsafe {label}: {value}")
    return candidate


def noise_output_target(source: Path, *, noise_root: Path) -> Path:
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", source.stem).strip("._") or "runtime_sample"
    noise_root.mkdir(parents=True, exist_ok=True)
    target = noise_root / f"{stem}.wav"
    counter = 1
    while target.exists():
        target = noise_root / f"{stem}_{counter}.wav"
        counter += 1
    return target


def noise_output_target_for_snr(
    source: Path,
    *,
    snr_db: float,
    noise_mode: str,
    noise_root: Path,
) -> Path:
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", source.stem).strip("._") or "runtime_sample"
    mode_label = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(noise_mode or "white")).strip("._") or "white"
    snr_label = str(float(snr_db)).replace(".", "p").replace("-", "m")
    noise_root.mkdir(parents=True, exist_ok=True)
    target = noise_root / f"{stem}_{mode_label}_snr{snr_label}.wav"
    counter = 1
    while target.exists():
        target = noise_root / f"{stem}_{mode_label}_snr{snr_label}_{counter}.wav"
        counter += 1
    return target
