#!/usr/bin/env python3
"""Run the extended multi-dataset thesis benchmark layer."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON_CMD = str(PYTHON) if PYTHON.exists() else sys.executable
SCENARIOS = ("embedded", "batch", "analytics", "dialog")
LOCAL_PROVIDERS = ("providers/whisper_local", "providers/vosk_local", "providers/huggingface_local")
CLOUD_PROVIDERS = ("providers/azure_cloud", "providers/google_cloud", "providers/aws_cloud", "providers/huggingface_api")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.credential_discovery import apply_discovered_environment, discover_credentials, write_credential_reports


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )
    return result


def _repo_relative(path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return str(path)
    try:
        return str(candidate.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def _sanitize_text(value: str) -> str:
    return value.replace(str(PROJECT_ROOT) + "/", "").replace(str(PROJECT_ROOT), ".")


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    datasets = payload.get("datasets", []) if isinstance(payload, dict) else []
    return [item for item in datasets if isinstance(item, dict)]


def _available_cloud_providers() -> list[str]:
    discovery = discover_credentials()
    available: list[str] = []
    for item in discovery.get("providers", []):
        provider = str(item.get("provider", "") or "")
        if item.get("config_complete"):
            available.append(f"providers/{provider}")
    return [provider for provider in CLOUD_PROVIDERS if provider in available]


def _run_benchmark(*, dataset_id: str, providers: list[str], run_id: str, cloud: bool) -> dict[str, Any]:
    profile = "thesis_extended_cloud_matrix" if cloud else "thesis_extended_local_matrix"
    result = _run(
        [
            PYTHON_CMD,
            "scripts/run_benchmark_core.py",
            "--benchmark-profile",
            profile,
            "--dataset-profile",
            f"datasets/{dataset_id}",
            "--providers",
            ",".join(providers),
            "--run-id",
            run_id,
            "--configs-root",
            str(PROJECT_ROOT / "configs"),
            "--artifact-root",
            str(PROJECT_ROOT / "artifacts"),
            "--registry-path",
            str(PROJECT_ROOT / "datasets" / "registry" / "datasets_extended.json"),
            "--results-dir",
            str(PROJECT_ROOT / "results" / "archive_legacy" / "extended_compat"),
        ],
        check=False,
    )
    payload: dict[str, Any] = {
        "dataset_id": dataset_id,
        "run_id": run_id,
        "providers": providers,
        "returncode": result.returncode,
        "stdout": _sanitize_text(result.stdout[-4000:]),
        "stderr": _sanitize_text(result.stderr[-4000:]),
    }
    if result.returncode == 0:
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload.update(_sanitize_payload(parsed))
        except json.JSONDecodeError:
            payload["parse_error"] = "benchmark stdout was not JSON"
    return payload


def _collect_schema_metrics(run_dir: str, raw_run_id: str) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    runs_ext = PROJECT_ROOT / "results" / "runs_ext"
    runs_ext.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        schema_run_id = f"{raw_run_id}_{scenario}"
        result = _run(
            [
                PYTHON_CMD,
                "scripts/collect_metrics.py",
                "--input",
                run_dir,
                "--results-dir",
                str(PROJECT_ROOT / "results"),
                "--run-id",
                schema_run_id,
                "--scenario",
                scenario,
                "--normalization-profile",
                "normalized-v1",
            ],
            check=False,
        )
        payload: dict[str, Any] = {
            "run_id": schema_run_id,
            "returncode": result.returncode,
            "stdout": _sanitize_text(result.stdout[-2000:]),
            "stderr": _sanitize_text(result.stderr[-2000:]),
        }
        source_dir = PROJECT_ROOT / "results" / "runs" / schema_run_id
        target_dir = runs_ext / schema_run_id
        if source_dir.exists():
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(source_dir), str(target_dir))
            payload["run_dir"] = _repo_relative(target_dir)
        outputs.append(payload)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run extended multi-dataset thesis benchmark")
    parser.add_argument("--mode", choices=["local", "cloud", "full"], default="full")
    parser.add_argument("--datasets", default="", help="Comma-separated dataset_id subset")
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args()

    apply_discovered_environment()
    _run(
        [
            PYTHON_CMD,
            "scripts/validate_dataset_assets.py",
            "--registry",
            "datasets/registry/datasets_extended.json",
            "--root",
            ".",
            "--output-md",
            "reports/datasets/dataset_asset_validation_extended.md",
            "--output-json",
            "reports/datasets/dataset_asset_validation_extended.json",
        ]
    )
    write_credential_reports()

    selected = {item.strip() for item in args.datasets.split(",") if item.strip()}
    datasets = [
        item for item in _load_registry(PROJECT_ROOT / "datasets" / "registry" / "datasets_extended.json")
        if not selected or str(item.get("dataset_id", "")) in selected
    ]
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    completed: list[dict[str, Any]] = []

    if args.mode in {"local", "full"}:
        for dataset in datasets:
            dataset_id = str(dataset["dataset_id"])
            run_id = f"thesis_ext_{timestamp}_local_{dataset_id}"
            payload = _run_benchmark(dataset_id=dataset_id, providers=list(LOCAL_PROVIDERS), run_id=run_id, cloud=False)
            if payload.get("returncode") == 0 and payload.get("run_dir"):
                payload["schema_runs"] = _collect_schema_metrics(str(payload["run_dir"]), run_id)
            completed.append({"kind": "local", **payload})

    if args.mode in {"cloud", "full"}:
        providers = _available_cloud_providers()
        for dataset in datasets:
            dataset_id = str(dataset["dataset_id"])
            run_id = f"thesis_ext_{timestamp}_cloud_{dataset_id}"
            if providers:
                payload = _run_benchmark(dataset_id=dataset_id, providers=providers, run_id=run_id, cloud=True)
                if payload.get("returncode") == 0 and payload.get("run_dir"):
                    payload["schema_runs"] = _collect_schema_metrics(str(payload["run_dir"]), run_id)
            else:
                payload = {
                    "dataset_id": dataset_id,
                    "run_id": run_id,
                    "providers": [],
                    "returncode": 0,
                    "skipped": True,
                    "skip_reason": "no complete cloud provider credentials detected",
                }
            completed.append({"kind": "cloud", **payload})

    run_manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": args.mode,
        "datasets": [item.get("dataset_id") for item in datasets],
        "completed": completed,
    }
    manifest_path = PROJECT_ROOT / "results" / "thesis_extended" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    if not args.skip_export:
        _run(
            [
                PYTHON_CMD,
                "scripts/export_thesis_extended_tables.py",
                "--input",
                "artifacts/benchmark_runs",
                "--output",
                "results/thesis_extended",
            ]
        )

    print(json.dumps({"created_at": datetime.now(UTC).isoformat(), "manifest": _repo_relative(manifest_path), "completed": len(completed)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
