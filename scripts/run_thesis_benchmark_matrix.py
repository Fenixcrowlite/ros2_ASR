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
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON_CMD = str(PYTHON) if PYTHON.exists() else sys.executable
SCENARIOS = ("embedded", "batch", "analytics", "dialog")
LOCAL_PROVIDERS = (
    "providers/whisper_local",
    "providers/vosk_local",
    "providers/huggingface_local",
)
CLOUD_PROVIDER_ENV = {
    "providers/huggingface_api": ("HF_TOKEN",),
    "providers/azure_cloud": ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"),
    "providers/google_cloud": ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT"),
    "providers/aws_cloud": ("AWS_TRANSCRIBE_BUCKET",),
}


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
    states: dict[str, dict[str, str]] = {}
    for provider, required_env in CLOUD_PROVIDER_ENV.items():
        provider_states: dict[str, str] = {}
        for key in required_env:
            value = os.getenv(key, "").strip()
            if key == "GOOGLE_APPLICATION_CREDENTIALS" and value:
                provider_states[key] = "available" if Path(value).expanduser().exists() else "invalid"
            else:
                provider_states[key] = "available" if value else "missing"
        if provider == "providers/aws_cloud":
            has_profile = bool(os.getenv("AWS_PROFILE", "").strip())
            has_keys = bool(os.getenv("AWS_ACCESS_KEY_ID", "").strip() and os.getenv("AWS_SECRET_ACCESS_KEY", "").strip())
            provider_states["AWS_AUTH"] = "available" if has_profile or has_keys else "missing"
            provider_states["AWS_REGION"] = "available" if os.getenv("AWS_REGION", "").strip() else "missing"
        states[provider] = provider_states
    return states


def _available_cloud_providers() -> list[str]:
    states = _credential_state()
    available: list[str] = []
    for provider, provider_states in states.items():
        if provider == "providers/aws_cloud":
            required = ("AWS_TRANSCRIBE_BUCKET", "AWS_AUTH", "AWS_REGION")
        else:
            required = CLOUD_PROVIDER_ENV[provider]
        if all(provider_states.get(key) == "available" for key in required):
            available.append(provider)
    return available


def _write_credential_report(path: Path) -> None:
    states = _credential_state()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Credential Availability",
        "",
        f"Created: `{datetime.now(UTC).isoformat()}`",
        "",
        "| Provider | Requirement | State |",
        "|---|---|---|",
    ]
    for provider, provider_states in sorted(states.items()):
        for key, state in sorted(provider_states.items()):
            lines.append(f"| {provider} | {key} | {state} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "thesis_final": str(PROJECT_ROOT / "results" / "thesis_final"),
    }
    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
