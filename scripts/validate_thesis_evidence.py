#!/usr/bin/env python3
"""Validate final thesis evidence traceability."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REQUIRED_FINAL_TABLES = [
    "provider_comparison.csv",
    "provider_smoke_tests.csv",
    "quality_table.csv",
    "performance_table.csv",
    "resource_table.csv",
    "noise_robustness_table.csv",
    "cost_deployment_table.csv",
    "scenario_scores.csv",
]
NON_EMPTY_TABLES = [
    "quality_table.csv",
    "performance_table.csv",
    "noise_robustness_table.csv",
    "cost_deployment_table.csv",
    "scenario_scores.csv",
]
EVIDENCE_TEXT_GLOBS = [
    ".ai/reports/current_task_report.md",
    "reports/datasets/**/*.md",
    "reports/datasets/**/*.json",
    "reports/thesis_test/**/*.md",
    "reports/thesis_test/**/*.json",
    "results/runs/**/*.md",
    "results/runs/**/*.json",
    "results/runs/**/*.csv",
    "results/thesis_final/**/*.md",
    "results/thesis_final/**/*.json",
    "results/thesis_final/**/*.csv",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _canonical_paths_from_report(path: Path) -> list[str]:
    if not path.exists():
        return []
    paths: list[str] = []
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Canonical Benchmark Artifacts"
            continue
        if not in_section:
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            paths.append(match.group(1))
    return paths


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    dataset_report = root / "reports/datasets/dataset_asset_validation.json"
    if dataset_report.exists():
        dataset_payload = _load_json(dataset_report)
        add(
            "dataset validation report passed",
            bool(isinstance(dataset_payload, dict) and dataset_payload.get("passed") is True),
            str(dataset_report.relative_to(root)),
        )
    else:
        add("dataset validation report exists", False, str(dataset_report.relative_to(root)))

    runs_dir = root / "results/runs"
    for manifest in sorted(runs_dir.glob("*/manifest.json")):
        try:
            payload = _load_json(manifest)
        except json.JSONDecodeError as exc:
            add(f"{manifest.relative_to(root)} parses", False, str(exc))
            continue
        source = payload.get("source", {}) if isinstance(payload, dict) else {}
        if not isinstance(source, dict):
            add(f"{manifest.relative_to(root)} source object", False, "missing source")
            continue
        for key in ("input_path", "summary_json", "results_json"):
            value = str(source.get(key, "") or "")
            add(
                f"{manifest.relative_to(root)} source.{key} exists",
                bool(value) and _repo_path(root, value).exists(),
                value or "missing",
            )

    final_report = root / "results/thesis_final/final_report.md"
    canonical_paths = _canonical_paths_from_report(final_report)
    add("final_report canonical artifact list present", bool(canonical_paths), str(final_report.relative_to(root)))
    for value in canonical_paths:
        add(f"final_report artifact exists: {value}", _repo_path(root, value).exists(), value)

    thesis_dir = root / "results/thesis_final"
    for name in REQUIRED_FINAL_TABLES:
        add(f"final table exists: {name}", (thesis_dir / name).exists(), str((thesis_dir / name).relative_to(root)))
    add("provider_smoke_tests.csv exists", (thesis_dir / "provider_smoke_tests.csv").exists())

    for name in NON_EMPTY_TABLES:
        path = thesis_dir / name
        if path.exists():
            rows = _csv_rows(path)
            add(f"final table non-empty: {name}", bool(rows), f"{len(rows)} data rows")
        else:
            add(f"final table non-empty: {name}", False, "missing")

    mock_findings: list[str] = []
    for table in thesis_dir.glob("*.csv"):
        rows = _csv_rows(table)
        for row_index, row in enumerate(rows, start=2):
            provider = str(row.get("provider", "") or "").lower()
            backend = str(row.get("backend", "") or "").lower()
            if any(token in f"{provider} {backend}" for token in ("mock", "fake", "dummy")):
                mock_findings.append(f"{table.relative_to(root)}:{row_index}")
    add("no mock/fake providers in final result tables", not mock_findings, ", ".join(mock_findings[:20]))

    absolute_findings: list[str] = []
    for pattern in EVIDENCE_TEXT_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            if path.name in {"thesis_evidence_validation.md", "thesis_evidence_validation.json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/home/fenix/Desktop/ros2ws" in text:
                absolute_findings.append(str(path.relative_to(root)))
    add(
        "no repository-root absolute paths in final evidence files",
        not absolute_findings,
        ", ".join(absolute_findings[:20]),
    )

    return {
        "created_at": datetime.now(UTC).isoformat(),
        "root": ".",
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "canonical_artifacts": canonical_paths,
    }


def write_reports(root: Path, payload: dict[str, Any]) -> None:
    output_dir = root / "reports/thesis_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "thesis_evidence_validation.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Thesis Evidence Validation",
        "",
        f"Created: `{payload['created_at']}`",
        f"passed: {'true' if payload['passed'] else 'false'}",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        detail = str(check.get("detail", "") or "").replace("|", "\\|")
        lines.append(f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | {detail} |")
    (output_dir / "thesis_evidence_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    payload = validate(root)
    write_reports(root, payload)
    print(json.dumps({"passed": payload["passed"], "checks": len(payload["checks"])}, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
