#!/usr/bin/env python3
"""Run fair preset-tier thesis benchmarks and collect schema artifacts."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "ros2_ws" / "src"
for candidate in reversed([PROJECT_ROOT, *[path for path in SRC_ROOT.iterdir() if path.is_dir()]]):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from asr_benchmark_core import BenchmarkOrchestrator, BenchmarkRunRequest  # noqa: E402
from scripts.credential_discovery import apply_discovered_environment  # noqa: E402

PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON_CMD = str(PYTHON) if PYTHON.exists() else sys.executable
SCENARIOS = ("embedded", "batch", "analytics", "dialog")
TIERS = {
    "fast": "thesis_tier_fast",
    "balanced": "thesis_tier_balanced",
    "accurate": "thesis_tier_accurate",
}


def _apply_resource_guards() -> None:
    """Keep local ASR inference from exhausting the interactive workstation."""
    defaults = {
        "OMP_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
        "NUMEXPR_NUM_THREADS": "2",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
    try:
        os.nice(8)
    except OSError:
        pass


def _acquire_run_lock():
    lock_path = PROJECT_ROOT / ".ai" / "thesis_tiered_benchmark.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise SystemExit(
            f"Another tiered benchmark is already running; lock: {lock_path}"
        ) from exc
    lock_file.write(str(os.getpid()) + "\n")
    lock_file.flush()
    return lock_file


def _repo_relative_path(value: str | Path) -> str:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        return str(value)
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(value)


def _run_checked(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
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


def _collect_schema_metrics(canonical_run_dir: str, raw_run_id: str) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        schema_run_id = f"{raw_run_id}_{scenario}"
        stdout = _run_checked(
            [
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
        )
        payload = json.loads(stdout)
        if isinstance(payload, dict):
            outputs.append(payload)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tiered thesis benchmark profiles")
    parser.add_argument(
        "--tiers",
        default="fast,balanced,accurate",
        help="Comma-separated tiers: fast,balanced,accurate",
    )
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args()

    _apply_resource_guards()
    _lock_file = _acquire_run_lock()
    apply_discovered_environment()
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

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    orchestrator = BenchmarkOrchestrator(
        configs_root=str(PROJECT_ROOT / "configs"),
        artifact_root=str(PROJECT_ROOT / "artifacts"),
        registry_path=str(PROJECT_ROOT / "datasets" / "registry" / "datasets.json"),
    )
    completed: list[dict[str, Any]] = []
    for raw_tier in args.tiers.split(","):
        tier = raw_tier.strip()
        if not tier:
            continue
        if tier not in TIERS:
            raise SystemExit(f"Unsupported tier: {tier}")
        run_id = f"thesis_{tier}_{timestamp}"
        summary = orchestrator.run(
            BenchmarkRunRequest(
                benchmark_profile=f"benchmark/{TIERS[tier]}",
                run_id=run_id,
            )
        )
        run_dir = Path(str(summary.metadata.get("run_dir", "") or "")).resolve()
        completed.append(
            {
                "tier": tier,
                "run_id": run_id,
                "total_samples": summary.total_samples,
                "successful_samples": summary.successful_samples,
                "failed_samples": summary.failed_samples,
                "run_dir": _repo_relative_path(run_dir),
                "schema_runs": _collect_schema_metrics(str(run_dir), run_id),
            }
        )

    if not args.skip_export:
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

    print(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "completed": completed,
                "thesis_final": "results/thesis_final",
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
