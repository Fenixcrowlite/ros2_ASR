#!/usr/bin/env python3
"""Run provider availability and one-utterance smoke checks for thesis artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
import time
import wave
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "ros2_ws" / "src"
for candidate in reversed([PROJECT_ROOT, *[path for path in SRC_ROOT.iterdir() if path.is_dir()]]):
    text = str(candidate)
    if text not in os.sys.path:
        os.sys.path.insert(0, text)

from asr_provider_base import ProviderAudio, ProviderManager  # noqa: E402
from asr_core.ids import make_request_id, make_session_id  # noqa: E402


FIELDS = [
    "provider",
    "model_or_preset",
    "available",
    "success",
    "latency_ms",
    "end_to_end_rtf",
    "text_preview",
    "error_type",
    "error_message_sanitized",
]

PROVIDERS = [
    {"provider": "whisper_local", "profile": "providers/whisper_local", "preset": "light"},
    {"provider": "vosk_local", "profile": "providers/vosk_local", "preset": "en_small"},
    {"provider": "huggingface_local", "profile": "providers/huggingface_local", "preset": "light"},
    {"provider": "huggingface_api", "profile": "providers/huggingface_api", "preset": ""},
    {"provider": "azure_cloud", "profile": "providers/azure_cloud", "preset": "standard"},
    {"provider": "google_cloud", "profile": "providers/google_cloud", "preset": ""},
    {"provider": "aws_cloud", "profile": "providers/aws_cloud", "preset": "standard"},
]


def _repo_relative_path(value: str | Path) -> str:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        return str(value)
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(value)


def _sanitize_error(message: str) -> str:
    sanitized = str(message or "").replace("\n", " ").replace("\r", " ")
    for key, value in os.environ.items():
        if any(token in key.upper() for token in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            if value and len(value) >= 4:
                sanitized = sanitized.replace(value, "<redacted>")
    sanitized = sanitized.replace(str(PROJECT_ROOT), ".")
    home = os.path.expanduser("~")
    if home:
        sanitized = sanitized.replace(home, "~")
    return " ".join(sanitized.split())[:400]


def _credential_problem(provider: str) -> tuple[bool, str]:
    required: dict[str, str] = {
        "huggingface_api": "HF_TOKEN",
        "azure_cloud": "AZURE_SPEECH_KEY,AZURE_SPEECH_REGION",
        "google_cloud": "GOOGLE_APPLICATION_CREDENTIALS,GOOGLE_CLOUD_PROJECT",
        "aws_cloud": "AWS_TRANSCRIBE_BUCKET,AWS_REGION,AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY",
    }
    if provider not in required:
        return False, ""
    if provider == "huggingface_api":
        return (not bool(os.getenv("HF_TOKEN", "").strip()), "HF_TOKEN")
    if provider == "azure_cloud":
        missing = [
            key
            for key in ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION")
            if not os.getenv(key, "").strip()
        ]
        return (bool(missing), ",".join(missing))
    if provider == "google_cloud":
        missing = [
            key
            for key in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT")
            if not os.getenv(key, "").strip()
        ]
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if credentials_path and not Path(credentials_path).expanduser().exists():
            missing.append("GOOGLE_APPLICATION_CREDENTIALS:invalid")
        return (bool(missing), ",".join(missing))
    if provider == "aws_cloud":
        missing = [
            key
            for key in ("AWS_TRANSCRIBE_BUCKET", "AWS_REGION")
            if not os.getenv(key, "").strip()
        ]
        has_profile = bool(os.getenv("AWS_PROFILE", "").strip())
        has_keys = bool(
            os.getenv("AWS_ACCESS_KEY_ID", "").strip()
            and os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
        )
        if not has_profile and not has_keys:
            missing.append("AWS_AUTH")
        return (bool(missing), ",".join(missing))
    return False, ""


def _sample_rate_hz(wav_path: Path) -> int:
    with wave.open(str(wav_path), "rb") as handle:
        return int(handle.getframerate())


def _load_sample(manifest_path: Path, sample_index: int) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise SystemExit(f"Dataset manifest is empty: {manifest_path}")
    row = rows[min(sample_index, len(rows) - 1)]
    audio_path = Path(str(row.get("audio_path", "") or ""))
    if not audio_path.is_absolute():
        audio_path = manifest_path.parent / audio_path
    if not audio_path.exists():
        raise SystemExit(f"Smoke audio is missing: {_repo_relative_path(audio_path)}")
    return {
        "wav_path": audio_path,
        "language": str(row.get("language", "") or "en-US"),
        "duration_sec": float(row.get("duration_sec") or 0.0),
    }


def _provider_worker(
    queue: mp.Queue,
    provider_spec: dict[str, str],
    sample: dict[str, Any],
) -> None:
    provider = provider_spec["provider"]
    preset = provider_spec["preset"]
    row: dict[str, Any] = {
        "provider": provider,
        "model_or_preset": preset,
        "available": True,
        "success": False,
        "latency_ms": "",
        "end_to_end_rtf": "",
        "text_preview": "",
        "error_type": "",
        "error_message_sanitized": "",
    }
    adapter = None
    started = time.perf_counter()
    try:
        manager = ProviderManager(configs_root=str(PROJECT_ROOT / "configs"))
        adapter = manager.create_from_profile(provider_spec["profile"], preset_id=preset)
        result = adapter.recognize_once(
            ProviderAudio(
                session_id=make_session_id(),
                request_id=make_request_id(),
                language=str(sample["language"]),
                sample_rate_hz=_sample_rate_hz(Path(sample["wav_path"])),
                wav_path=str(sample["wav_path"]),
                enable_word_timestamps=True,
            )
        )
        latency_ms = max((time.perf_counter() - started) * 1000.0, 0.0)
        duration_sec = float(sample.get("duration_sec") or 0.0)
        row.update(
            {
                "success": not result.degraded and not result.error_code,
                "latency_ms": latency_ms,
                "end_to_end_rtf": (latency_ms / 1000.0 / duration_sec)
                if duration_sec > 0.0
                else "",
                "text_preview": " ".join(str(result.text or "").split())[:120],
                "error_type": result.error_code,
                "error_message_sanitized": _sanitize_error(result.error_message),
            }
        )
        if not row["success"] and not row["error_type"]:
            row["error_type"] = "provider_error"
    except Exception as exc:  # noqa: BLE001 - smoke table must capture all provider failures.
        row.update(
            {
                "success": False,
                "latency_ms": max((time.perf_counter() - started) * 1000.0, 0.0),
                "error_type": type(exc).__name__,
                "error_message_sanitized": _sanitize_error(str(exc)),
            }
        )
    finally:
        if adapter is not None:
            try:
                adapter.teardown()
            except Exception:
                pass
        queue.put(row)


def _csv_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value) if value is not None else ""


def _run_smoke(provider_spec: dict[str, str], sample: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    missing, detail = _credential_problem(provider_spec["provider"])
    if missing:
        return {
            "provider": provider_spec["provider"],
            "model_or_preset": provider_spec["preset"],
            "available": False,
            "success": False,
            "latency_ms": "",
            "end_to_end_rtf": "",
            "text_preview": "",
            "error_type": "missing_credentials",
            "error_message_sanitized": detail,
        }

    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_provider_worker, args=(queue, provider_spec, sample))
    process.start()
    process.join(timeout_sec)
    if process.is_alive():
        process.terminate()
        process.join(5)
        return {
            "provider": provider_spec["provider"],
            "model_or_preset": provider_spec["preset"],
            "available": True,
            "success": False,
            "latency_ms": timeout_sec * 1000,
            "end_to_end_rtf": "",
            "text_preview": "",
            "error_type": "timeout",
            "error_message_sanitized": f"provider smoke test exceeded {timeout_sec} seconds",
        }
    if not queue.empty():
        return dict(queue.get())
    return {
        "provider": provider_spec["provider"],
        "model_or_preset": provider_spec["preset"],
        "available": True,
        "success": False,
        "latency_ms": "",
        "end_to_end_rtf": "",
        "text_preview": "",
        "error_type": "no_result",
        "error_message_sanitized": "provider process exited without a smoke result",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run thesis provider smoke tests")
    parser.add_argument("--output", default="results/thesis_final/provider_smoke_tests.csv")
    parser.add_argument(
        "--dataset-manifest",
        default="datasets/manifests/librispeech_test_clean_subset.jsonl",
    )
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--timeout-sec", type=int, default=120)
    args = parser.parse_args()

    manifest_path = PROJECT_ROOT / args.dataset_manifest
    sample = _load_sample(manifest_path, args.sample_index)
    rows = [_run_smoke(provider, sample, args.timeout_sec) for provider in PROVIDERS]

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in FIELDS})

    print(
        json.dumps(
            {
                "output": _repo_relative_path(output_path),
                "providers": len(rows),
                "success": sum(1 for row in rows if row.get("success") is True),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
