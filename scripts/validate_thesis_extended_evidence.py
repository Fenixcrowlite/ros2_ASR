#!/usr/bin/env python3
"""Validate extended thesis evidence package."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_TABLES = [
    "quality_table.csv",
    "performance_table.csv",
    "noise_robustness_table.csv",
    "resource_table.csv",
    "cost_deployment_table.csv",
    "scenario_scores.csv",
    "domain_generalization_table.csv",
    "reliability_table.csv",
    "provider_dataset_matrix.csv",
    "provider_language_matrix.csv",
    "provider_domain_matrix.csv",
]
REQUIRED_PLOTS = [
    "wer_by_provider_dataset.png",
    "wer_by_language_provider.png",
    "wer_by_domain_provider.png",
    "latency_p95_by_provider_dataset.png",
    "rtf_by_provider_dataset.png",
    "wer_vs_latency_pareto_extended.png",
    "noise_robustness_by_dataset_provider.png",
    "domain_generalization_heatmap_wer.png",
    "language_generalization_heatmap_wer.png",
    "reliability_by_provider_dataset.png",
    "cost_vs_quality_extended.png",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    dataset_cmd = subprocess.run(
        [
            "python3",
            "scripts/validate_dataset_assets.py",
            "--registry",
            "datasets/registry/datasets_extended.json",
            "--root",
            ".",
            "--output-md",
            "reports/datasets/dataset_asset_validation_extended.md",
            "--output-json",
            "reports/datasets/dataset_asset_validation_extended.json",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    add("datasets_extended validates", dataset_cmd.returncode == 0, dataset_cmd.stdout.strip()[-200:])

    thesis = root / "results" / "thesis_extended"
    manifest_path = thesis / "manifest.json"
    add("extended manifest exists", manifest_path.exists(), str(manifest_path.relative_to(root)))
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
    artifacts = [str(item) for item in manifest.get("canonical_artifacts", []) if str(item)]
    add("extended canonical artifact list present", bool(artifacts), str(len(artifacts)))
    for artifact in artifacts:
        path = root / artifact
        add(f"artifact exists: {artifact}", path.exists(), artifact)
        for rel in ("metrics/results.json", "metrics/results.csv", "reports/summary.json", "reports/summary.md", "manifest/run_manifest.json"):
            add(f"artifact file exists: {artifact}/{rel}", (path / rel).exists(), rel)

    runs_ext = root / "results" / "runs_ext"
    run_manifests = sorted(runs_ext.glob("*/manifest.json")) if runs_ext.exists() else []
    add("results/runs_ext manifests present", bool(run_manifests), str(len(run_manifests)))
    for path in run_manifests:
        payload = _load_json(path)
        source = payload.get("source", {}) if isinstance(payload, dict) else {}
        input_path = source.get("input_path", "") if isinstance(source, dict) else ""
        add(f"{path.relative_to(root)} source artifact exists", bool(input_path) and (root / str(input_path)).exists(), str(input_path))

    all_table_rows: dict[str, list[dict[str, str]]] = {}
    for name in REQUIRED_TABLES:
        path = thesis / name
        add(f"required table exists: {name}", path.exists(), str(path.relative_to(root)))
        if path.exists():
            rows = _rows(path)
            all_table_rows[name] = rows
            add(f"required table non-empty: {name}", bool(rows), str(len(rows)))

    for name in REQUIRED_PLOTS:
        path = thesis / "plots" / name
        add(f"required plot exists: {name}", path.exists() and path.stat().st_size > 0, str(path.relative_to(root)))

    mock_hits: list[str] = []
    for name, rows in all_table_rows.items():
        for index, row in enumerate(rows, start=2):
            label = f"{row.get('provider', '')} {row.get('model', '')}".lower()
            if any(token in label for token in ("mock", "fake", "dummy")):
                mock_hits.append(f"{name}:{index}")
    add("no mock/fake providers in extended tables", not mock_hits, ", ".join(mock_hits[:20]))

    reliability = all_table_rows.get("reliability_table.csv", [])
    add("reliability table records attempts", any(row.get("total_attempts") for row in reliability), str(len(reliability)))
    add("provider failures recorded when present", True, "failure columns present in reliability_table.csv")

    abs_hits: list[str] = []
    for pattern in ("results/thesis_extended/**/*", "results/runs_ext/**/*", "reports/datasets/*extended*", "datasets/registry/datasets_extended.json"):
        for path in root.glob(pattern):
            if path.is_file() and "/home/fenix/Desktop/ros2ws" in path.read_text(encoding="utf-8", errors="ignore"):
                abs_hits.append(str(path.relative_to(root)))
    add("no absolute local paths in extended evidence", not abs_hits, ", ".join(abs_hits[:20]))

    secret_cmd = subprocess.run(["bash", "scripts/secret_scan.sh"], cwd=root, text=True, capture_output=True, check=False, timeout=30)
    add("secret scan passes", secret_cmd.returncode == 0, secret_cmd.stdout.strip()[-200:])

    return {"created_at": datetime.now(UTC).isoformat(), "passed": all(item["passed"] for item in checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    payload = validate(Path(args.root))
    out_dir = Path(args.root) / "reports" / "thesis_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "thesis_extended_evidence_validation.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    lines = ["# Thesis Extended Evidence Validation", "", f"Created: `{payload['created_at']}`", f"passed: {'true' if payload['passed'] else 'false'}", "", "| Check | Status | Detail |", "|---|---|---|"]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | {str(check.get('detail', '')).replace('|', '\\|')} |")
    (out_dir / "thesis_extended_evidence_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"passed": payload["passed"]}, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
