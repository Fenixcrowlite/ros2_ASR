"""Helpers for benchmark result discovery and comparison views."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from fastapi import HTTPException

ReadJsonFn = Callable[[Path, Any], Any]
CleanNameFn = Callable[[str, str], str]
RunDetailLoader = Callable[[str], dict[str, Any]]
MetricPreferenceFn = Callable[[str], str]


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def run_dir(artifacts_root: Path, run_id: str, *, clean_name: CleanNameFn) -> Path:
    rid = clean_name(run_id, "run_id")
    return artifacts_root / "benchmark_runs" / rid


def list_benchmark_history(
    *,
    artifacts_root: Path,
    read_json: ReadJsonFn,
    benchmark_jobs: Mapping[str, dict[str, Any]],
    limit: int = 50,
) -> list[dict[str, Any]]:
    root = artifacts_root / "benchmark_runs"
    if not root.exists():
        return []

    rows: list[dict[str, Any]] = []
    run_dirs = [path for path in root.iterdir() if path.is_dir()]
    run_dirs.sort(key=_safe_mtime, reverse=True)

    for run_dir_path in run_dirs[:limit]:
        run_id = run_dir_path.name
        summary = read_json(run_dir_path / "reports" / "summary.json", {})
        run_manifest = read_json(run_dir_path / "manifest" / "run_manifest.json", {})
        job = benchmark_jobs.get(run_id, {})
        state = str(job.get("state", "completed" if summary else "unknown"))

        rows.append(
            {
                "run_id": run_id,
                "state": state,
                "started_at": job.get("started_at", run_manifest.get("created_at", "")),
                "completed_at": job.get("completed_at", ""),
                "benchmark_profile": run_manifest.get("benchmark_profile", ""),
                "dataset_profile": run_manifest.get("dataset_profile", ""),
                "scenario": run_manifest.get("scenario", summary.get("scenario", "")),
                "execution_mode": summary.get(
                    "execution_mode",
                    run_manifest.get("execution_mode", "batch"),
                ),
                "providers": run_manifest.get("providers", []),
                "total_samples": summary.get("total_samples", run_manifest.get("sample_count", 0)),
                "successful_samples": summary.get("successful_samples", 0),
                "failed_samples": summary.get("failed_samples", 0),
                "mean_metrics": summary.get("mean_metrics", {}),
                "quality_metrics": summary.get("quality_metrics", {}),
                "resource_metrics": summary.get("resource_metrics", {}),
                "run_dir": str(run_dir_path),
            }
        )

    existing_ids = {row["run_id"] for row in rows}
    for run_id, state in benchmark_jobs.items():
        if run_id in existing_ids:
            continue
        rows.insert(
            0,
            {
                "run_id": run_id,
                "state": state.get("state", "unknown"),
                "started_at": state.get("started_at", ""),
                "completed_at": state.get("completed_at", ""),
                "benchmark_profile": state.get("benchmark_profile", ""),
                "dataset_profile": state.get("dataset_profile", ""),
                "scenario": state.get("scenario", ""),
                "execution_mode": state.get("execution_mode", "batch"),
                "providers": state.get("providers", []),
                "total_samples": 0,
                "successful_samples": 0,
                "failed_samples": 0,
                "mean_metrics": {},
                "quality_metrics": {},
                "resource_metrics": {},
                "run_dir": "",
            },
        )

    return rows[:limit]


def run_detail(
    run_id: str,
    *,
    artifacts_root: Path,
    clean_name: CleanNameFn,
    read_json: ReadJsonFn,
    benchmark_jobs: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    run_dir_path = run_dir(artifacts_root, run_id, clean_name=clean_name)
    if not run_dir_path.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    run_manifest = read_json(run_dir_path / "manifest" / "run_manifest.json", {})
    summary = read_json(run_dir_path / "reports" / "summary.json", {})
    metrics_rows = read_json(run_dir_path / "metrics" / "results.json", [])
    results_head = metrics_rows[:100] if isinstance(metrics_rows, list) else []
    results_count = len(metrics_rows) if isinstance(metrics_rows, list) else 0
    state = benchmark_jobs.get(run_id, {}).get("state", "completed")

    return {
        "run_id": run_id,
        "state": state,
        "run_manifest": run_manifest,
        "summary": summary,
        "results_head": results_head,
        "results_count": results_count,
        "artifacts": {
            "manifest": str(run_dir_path / "manifest" / "run_manifest.json"),
            "summary_json": str(run_dir_path / "reports" / "summary.json"),
            "summary_md": str(run_dir_path / "reports" / "summary.md"),
            "results_json": str(run_dir_path / "metrics" / "results.json"),
            "results_csv": str(run_dir_path / "metrics" / "results.csv"),
        },
    }


def metric_preference(metric_name: str) -> str:
    lowered = metric_name.lower()
    lower_is_better_tokens = ("wer", "cer", "latency", "error", "failure", "timeout", "rtf")
    if any(token in lowered for token in lower_is_better_tokens):
        return "lower"
    return "higher"


def compare_runs(
    run_ids: list[str],
    metrics: list[str],
    *,
    detail_loader: RunDetailLoader,
    metric_preference_func: MetricPreferenceFn = metric_preference,
) -> dict[str, Any]:
    if not run_ids:
        raise HTTPException(status_code=400, detail="run_ids must not be empty")

    details = [detail_loader(run_id) for run_id in run_ids]
    summaries = [detail.get("summary", {}) for detail in details]

    metric_names = sorted(
        set(metrics)
        if metrics
        else {
            key
            for summary in summaries
            for key in (summary.get("mean_metrics", {}) or {}).keys()
        }
    )

    by_run: dict[str, dict[str, float]] = {}
    for detail in details:
        result_run_id = str(detail.get("run_id", ""))
        mean_metrics = detail.get("summary", {}).get("mean_metrics", {})
        row: dict[str, float] = {}
        for metric in metric_names:
            value = mean_metrics.get(metric)
            if value is None:
                continue
            row[metric] = float(value)
        by_run[result_run_id] = row

    table: list[dict[str, Any]] = []
    for metric in metric_names:
        values = {run_id: by_run.get(run_id, {}).get(metric) for run_id in run_ids}
        available = {run_id: val for run_id, val in values.items() if val is not None}
        best_run = ""
        if available:
            if metric_preference_func(metric) == "lower":
                best_run = min(available, key=available.get)
            else:
                best_run = max(available, key=available.get)

        table.append(
            {
                "metric": metric,
                "preference": metric_preference_func(metric),
                "values": values,
                "best_run": best_run,
            }
        )

    return {
        "run_ids": run_ids,
        "metrics": metric_names,
        "by_run": by_run,
        "table": table,
    }
