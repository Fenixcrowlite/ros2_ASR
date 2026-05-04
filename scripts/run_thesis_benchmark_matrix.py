#!/usr/bin/env python3
"""Run thesis benchmark matrices and export final thesis artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.credential_discovery import (
    apply_discovered_environment,
    discover_credentials,
    write_credential_reports,
)

PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON_CMD = str(PYTHON) if PYTHON.exists() else sys.executable
SCENARIOS = ("embedded", "batch", "analytics", "dialog")
LOCAL_PROVIDERS = (
    "providers/whisper_local",
    "providers/vosk_local",
    "providers/huggingface_local",
)
CLOUD_PROVIDER_ENV = {
    "providers/huggingface_api": ("HF_TOKEN or HUGGINGFACEHUB_API_TOKEN",),
    "providers/azure_cloud": (
        "AZURE_SPEECH_KEY or SPEECH_KEY",
        "AZURE_SPEECH_REGION or SPEECH_REGION",
    ),
    "providers/google_cloud": (
        "GOOGLE_APPLICATION_CREDENTIALS or ADC",
        "GOOGLE_CLOUD_PROJECT or GCP_PROJECT",
    ),
    "providers/aws_cloud": (
        "AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY",
        "AWS_REGION or AWS_DEFAULT_REGION",
        "AWS_TRANSCRIBE_BUCKET or AWS_S3_BUCKET or ASR_AWS_S3_BUCKET",
    ),
}


def _repo_relative_path(value: str | Path) -> str:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        return str(value)
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(value)


def _run(command: list[str], *, cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _run_checked(command: list[str]) -> str:
    result = _run(command)
    if result.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )
    return result.stdout


def _credential_state() -> dict[str, dict[str, str]]:
    discovery = discover_credentials()
    states: dict[str, dict[str, str]] = {}
    for item in discovery.get("providers", []):
        provider_ref = f"providers/{item['provider']}"
        requirements = item.get("requirements", {})
        states[provider_ref] = dict(requirements) if isinstance(requirements, dict) else {}
        states[provider_ref]["credential_detected"] = (
            "available" if item.get("credential_detected") else "missing"
        )
        states[provider_ref]["config_complete"] = (
            "available" if item.get("config_complete") else "missing"
        )
    return states


def _available_cloud_providers() -> list[str]:
    discovery = discover_credentials()
    available: list[str] = []
    for item in discovery.get("providers", []):
        provider = str(item.get("provider", "") or "")
        if item.get("config_complete"):
            available.append(f"providers/{provider}")
    return available


def _write_credential_report(path: Path) -> None:
    del path
    write_credential_reports()


def _parse_run_payload(stdout: str) -> dict[str, Any]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Benchmark runner did not return JSON: {exc}\n{stdout}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Benchmark runner returned unsupported JSON payload")
    return payload


def _run_benchmark(
    *,
    profile: str,
    providers: list[str],
    run_id: str,
) -> dict[str, Any]:
    command = [
        PYTHON_CMD,
        "scripts/run_benchmark_core.py",
        "--benchmark-profile",
        profile,
        "--providers",
        ",".join(providers),
        "--run-id",
        run_id,
        "--configs-root",
        str(PROJECT_ROOT / "configs"),
        "--artifact-root",
        str(PROJECT_ROOT / "artifacts"),
        "--registry-path",
        str(PROJECT_ROOT / "datasets" / "registry" / "datasets.json"),
        "--results-dir",
        str(PROJECT_ROOT / "results"),
    ]
    stdout = _run_checked(command)
    return _parse_run_payload(stdout)


def _collect_schema_metrics(canonical_run_dir: str, raw_run_id: str) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        schema_run_id = f"{raw_run_id}_{scenario}"
        command = [
            PYTHON_CMD,
            "scripts/collect_metrics.py",
            "--input",
            canonical_run_dir,
            "--results-dir",
            str(PROJECT_ROOT / "results"),
            "--run-id",
            schema_run_id,
            "--scenario",
            scenario,
            "--normalization-profile",
            "normalized-v1",
        ]
        stdout = _run_checked(command)
        payload = json.loads(stdout)
        if isinstance(payload, dict):
            outputs.append(payload)
    return outputs


def _run_export() -> None:
    _run_checked(
        [
            PYTHON_CMD,
            "scripts/run_provider_smoke_tests.py",
            "--output",
            "results/thesis_final/provider_smoke_tests.csv",
        ]
    )
    _run_checked(
        [
            PYTHON_CMD,
            "scripts/export_thesis_tables.py",
            "--input",
            str(PROJECT_ROOT / "results" / "runs"),
            "--output",
            str(PROJECT_ROOT / "results" / "thesis_final"),
        ]
    )


def _run_dataset_validation() -> None:
    _run_checked(
        [
            PYTHON_CMD,
            "scripts/validate_dataset_assets.py",
            "--registry",
            "datasets/registry/datasets.json",
            "--root",
            ".",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run thesis benchmark matrices")
    parser.add_argument("--mode", choices=["local", "cloud", "full", "auto"], default="local")
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args()

    apply_discovered_environment()
    _run_dataset_validation()
    _write_credential_report(PROJECT_ROOT / "reports" / "thesis_test" / "credential_availability.md")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    completed: list[dict[str, Any]] = []

    if args.mode in {"local", "full", "auto"}:
        raw_run_id = f"thesis_local_{timestamp}"
        payload = _run_benchmark(
            profile="thesis_local_matrix",
            providers=list(LOCAL_PROVIDERS),
            run_id=raw_run_id,
        )
        completed.append(
            {
                "kind": "local",
                "benchmark": payload,
                "schema_runs": _collect_schema_metrics(str(payload["run_dir"]), raw_run_id),
            }
        )

    if args.mode in {"cloud", "full", "auto"}:
        cloud_providers = _available_cloud_providers()
        if cloud_providers:
            raw_run_id = f"thesis_cloud_{timestamp}"
            payload = _run_benchmark(
                profile="thesis_cloud_matrix",
                providers=cloud_providers,
                run_id=raw_run_id,
            )
            completed.append(
                {
                    "kind": "cloud",
                    "providers": cloud_providers,
                    "benchmark": payload,
                    "schema_runs": _collect_schema_metrics(str(payload["run_dir"]), raw_run_id),
                }
            )

    if not args.skip_export:
        _run_export()

    output = {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": args.mode,
        "completed": completed,
        "thesis_final": _repo_relative_path(PROJECT_ROOT / "results" / "thesis_final"),
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
