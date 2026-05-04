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

from asr_core.ids import make_request_id, make_session_id  # noqa: E402
from asr_provider_base import ProviderAudio, ProviderManager  # noqa: E402
from scripts.credential_discovery import (  # noqa: E402
    apply_discovered_environment,
    discover_credentials,
    write_credential_reports,
)

FIELDS = [
    "provider",
    "model_or_preset",
    "available",
    "credential_detected",
    "auth_probe_success",
    "smoke_recognition_success",
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
    discovery = discover_credentials()
    by_provider = {item["provider"]: item for item in discovery.get("providers", [])}
    state = by_provider.get(provider)
    if state is None:
        return False, ""
    if state.get("config_complete"):
        return False, ""
    requirements = state.get("requirements", {})
    missing = [key for key, status in requirements.items() if status != "available"]
    if state.get("credential_detected"):
        return True, "found_but_config_incomplete: missing " + ",".join(missing)
    return True, "missing_credentials: " + ",".join(missing)


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
        "credential_detected": True,
        "auth_probe_success": False,
        "smoke_recognition_success": False,
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
                "auth_probe_success": not result.degraded and not result.error_code,
                "smoke_recognition_success": not result.degraded and not result.error_code,
                "latency_ms": latency_ms,
                "end_to_end_rtf": (latency_ms / 1000.0 / duration_sec)
                if duration_sec > 0.0
                else "",
                "text_preview": " ".join(str(result.text or "").split())[:120],
                "error_type": result.error_code,
                "error_message_sanitized": _sanitize_error(result.error_message),
            }
        )
        if not row["smoke_recognition_success"] and not row["error_type"]:
            row["error_type"] = "provider_error"
    except Exception as exc:  # noqa: BLE001 - smoke table must capture all provider failures.
        row.update(
            {
                "auth_probe_success": False,
                "smoke_recognition_success": False,
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
        credential_detected = not detail.startswith("missing_credentials:")
        return {
            "provider": provider_spec["provider"],
            "model_or_preset": provider_spec["preset"],
            "available": True,
            "credential_detected": credential_detected,
            "auth_probe_success": False,
            "smoke_recognition_success": False,
            "latency_ms": "",
            "end_to_end_rtf": "",
            "text_preview": "",
            "error_type": "found_but_config_incomplete"
            if credential_detected
            else "missing_credentials",
            "error_message_sanitized": detail.split(":", 1)[-1].strip(),
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
            "credential_detected": True,
            "auth_probe_success": False,
            "smoke_recognition_success": False,
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
        "credential_detected": True,
        "auth_probe_success": False,
        "smoke_recognition_success": False,
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

    apply_discovered_environment()
    manifest_path = PROJECT_ROOT / args.dataset_manifest
    sample = _load_sample(manifest_path, args.sample_index)
    rows = [_run_smoke(provider, sample, args.timeout_sec) for provider in PROVIDERS]
    write_credential_reports(smoke_rows=rows)

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
                "success": sum(
                    1 for row in rows if row.get("smoke_recognition_success") is True
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
