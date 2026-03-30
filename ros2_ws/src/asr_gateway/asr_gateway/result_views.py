"""Helpers for benchmark result discovery and comparison views."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from asr_config import resolve_profile
from asr_datasets import DatasetRegistry, load_manifest
from asr_metrics.definitions import metric_preference as metric_preference_from_registry
from asr_metrics.quality import text_quality_support
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


def _resolve_project_path(project_root: Path, path_ref: Any) -> Path | None:
    raw = str(path_ref or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = project_root / path
    return path


def _dataset_manifest_path(
    run_manifest: Mapping[str, Any],
    *,
    artifacts_root: Path,
    read_json: ReadJsonFn,
) -> Path | None:
    project_root = artifacts_root.parent
    candidates: list[Any] = [run_manifest.get("dataset_manifest")]

    config_snapshots = run_manifest.get("config_snapshots", {})
    if isinstance(config_snapshots, Mapping):
        snapshot_path = _resolve_project_path(project_root, config_snapshots.get("dataset"))
        if snapshot_path is not None and snapshot_path.exists():
            snapshot_payload = read_json(snapshot_path, {})
            if isinstance(snapshot_payload, Mapping):
                candidates.append(snapshot_payload.get("manifest_path"))

    dataset_profile = str(run_manifest.get("dataset_profile", "") or "").strip()
    if dataset_profile:
        dataset_profile_id = (
            dataset_profile.split("/", 1)[1]
            if dataset_profile.startswith("datasets/")
            else dataset_profile
        )
        try:
            resolved_dataset = resolve_profile(
                profile_type="datasets",
                profile_id=dataset_profile_id,
                configs_root=str(project_root / "configs"),
                write_snapshot=False,
            )
        except Exception:
            resolved_dataset = None
        if resolved_dataset is not None:
            candidates.append(resolved_dataset.data.get("manifest_path"))

        registry_path = project_root / "datasets" / "registry" / "datasets.json"
        if registry_path.exists():
            try:
                registry = DatasetRegistry(str(registry_path))
                for entry in registry.list():
                    entry_profile = str(entry.metadata.get("dataset_profile", "") or "")
                    if entry_profile == dataset_profile or entry.dataset_id == dataset_profile_id:
                        candidates.append(entry.manifest_ref)
            except Exception:
                pass

    for candidate in candidates:
        path = _resolve_project_path(project_root, candidate)
        if path is not None and path.exists():
            return path
    return None


def _reference_texts_by_sample(
    run_manifest: Mapping[str, Any],
    *,
    artifacts_root: Path,
    read_json: ReadJsonFn,
) -> dict[str, str]:
    manifest_path = _dataset_manifest_path(
        run_manifest,
        artifacts_root=artifacts_root,
        read_json=read_json,
    )
    if manifest_path is None:
        return {}

    try:
        samples = load_manifest(str(manifest_path))
    except Exception:
        return {}

    return {
        str(sample.sample_id): str(sample.transcript or "")
        for sample in samples
        if str(sample.sample_id or "").strip()
    }


def _enrich_result_row(
    row: Any,
    *,
    reference_texts_by_sample: Mapping[str, str],
) -> Any:
    if not isinstance(row, dict):
        return row

    enriched = dict(row)
    sample_id = str(enriched.get("sample_id", "") or "")
    reference_text = str(enriched.get("reference_text", "") or "")
    single_reference_text = (
        next(iter(reference_texts_by_sample.values()))
        if len(reference_texts_by_sample) == 1
        else ""
    )
    if not reference_text and sample_id:
        reference_text = str(reference_texts_by_sample.get(sample_id, "") or "")
    if not reference_text and single_reference_text:
        reference_text = single_reference_text
    if reference_text:
        enriched["reference_text"] = reference_text

    quality_support = enriched.get("quality_support")
    if isinstance(quality_support, Mapping):
        support_payload = dict(quality_support)
    elif reference_text:
        support_payload = text_quality_support(
            reference_text,
            str(enriched.get("text", "") or ""),
        ).as_dict()
        enriched["quality_support"] = support_payload
    else:
        support_payload = {}

    if support_payload:
        if not str(enriched.get("normalized_reference_text", "") or ""):
            enriched["normalized_reference_text"] = str(
                support_payload.get("normalized_reference", "") or ""
            )
        if not str(enriched.get("normalized_hypothesis_text", "") or ""):
            enriched["normalized_hypothesis_text"] = str(
                support_payload.get("normalized_hypothesis", "") or ""
            )

    return enriched


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
                "aggregate_scope": summary.get("aggregate_scope", "provider_only"),
                "providers": run_manifest.get("providers", []),
                "total_samples": summary.get("total_samples", run_manifest.get("sample_count", 0)),
                "successful_samples": summary.get("successful_samples", 0),
                "failed_samples": summary.get("failed_samples", 0),
                "mean_metrics": summary.get("mean_metrics", {}),
                "metric_statistics": summary.get("metric_statistics", {}),
                "metric_metadata": summary.get("metric_metadata", {}),
                "quality_metrics": summary.get("quality_metrics", {}),
                "latency_metrics": summary.get("latency_metrics", {}),
                "reliability_metrics": summary.get("reliability_metrics", {}),
                "cost_metrics": summary.get("cost_metrics", {}),
                "cost_totals": summary.get("cost_totals", {}),
                "streaming_metrics": summary.get("streaming_metrics", {}),
                "resource_metrics": summary.get("resource_metrics", {}),
                "provider_summaries": summary.get("provider_summaries", []),
                "run_dir": str(run_dir_path),
            }
        )

    existing_ids = {row["run_id"] for row in rows}
    for run_id, job_state in benchmark_jobs.items():
        if run_id in existing_ids:
            continue
        rows.insert(
            0,
            {
                "run_id": run_id,
                "state": job_state.get("state", "unknown"),
                "started_at": job_state.get("started_at", ""),
                "completed_at": job_state.get("completed_at", ""),
                "benchmark_profile": job_state.get("benchmark_profile", ""),
                "dataset_profile": job_state.get("dataset_profile", ""),
                "scenario": job_state.get("scenario", ""),
                "execution_mode": job_state.get("execution_mode", "batch"),
                "aggregate_scope": "provider_only",
                "providers": job_state.get("providers", []),
                "total_samples": 0,
                "successful_samples": 0,
                "failed_samples": 0,
                "mean_metrics": {},
                "metric_statistics": {},
                "metric_metadata": {},
                "quality_metrics": {},
                "latency_metrics": {},
                "reliability_metrics": {},
                "cost_metrics": {},
                "cost_totals": {},
                "streaming_metrics": {},
                "resource_metrics": {},
                "provider_summaries": [],
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
    reference_texts = _reference_texts_by_sample(
        run_manifest,
        artifacts_root=artifacts_root,
        read_json=read_json,
    )
    results_head = (
        [
            _enrich_result_row(
                row,
                reference_texts_by_sample=reference_texts,
            )
            for row in metrics_rows[:100]
        ]
        if isinstance(metrics_rows, list)
        else []
    )
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
    return metric_preference_from_registry(metric_name)


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
    subjects: list[dict[str, Any]] = []
    by_run: dict[str, dict[str, float]] = {}
    discovered_metric_names: set[str] = set()

    for detail in details:
        result_run_id = str(detail.get("run_id", ""))
        summary = detail.get("summary", {})
        provider_summaries = summary.get("provider_summaries", [])
        if isinstance(provider_summaries, list) and provider_summaries:
            for provider_summary in provider_summaries:
                if not isinstance(provider_summary, dict):
                    continue
                provider_key = str(
                    provider_summary.get("provider_key")
                    or provider_summary.get("provider_profile")
                    or provider_summary.get("provider_id")
                    or result_run_id
                )
                entity_id = f"{result_run_id}::{provider_key}"
                mean_metrics = provider_summary.get("mean_metrics", {})
                row: dict[str, float] = {}
                if isinstance(mean_metrics, dict):
                    for metric_name, value in mean_metrics.items():
                        if value is None:
                            continue
                        metric_key = str(metric_name or "").strip()
                        if not metric_key:
                            continue
                        row[metric_key] = float(value)
                        discovered_metric_names.add(metric_key)
                subjects.append(
                    {
                        "entity_id": entity_id,
                        "run_id": result_run_id,
                        "provider_key": provider_key,
                        "provider_profile": str(provider_summary.get("provider_profile", "") or ""),
                        "provider_id": str(provider_summary.get("provider_id", "") or ""),
                        "provider_preset": str(provider_summary.get("provider_preset", "") or ""),
                    }
                )
                by_run[entity_id] = row
            continue

        mean_metrics = summary.get("mean_metrics", {})
        row = {}
        if isinstance(mean_metrics, dict):
            for metric_name, value in mean_metrics.items():
                if value is None:
                    continue
                metric_key = str(metric_name or "").strip()
                if not metric_key:
                    continue
                row[metric_key] = float(value)
                discovered_metric_names.add(metric_key)
        subjects.append(
            {
                "entity_id": result_run_id,
                "run_id": result_run_id,
                "provider_key": "",
                "provider_profile": "",
                "provider_id": "",
                "provider_preset": "",
            }
        )
        by_run[result_run_id] = row

    metric_names = sorted(set(metrics) if metrics else discovered_metric_names)

    table: list[dict[str, Any]] = []
    entity_ids = [str(subject.get("entity_id", "")) for subject in subjects]
    for metric in metric_names:
        values = {entity_id: by_run.get(entity_id, {}).get(metric) for entity_id in entity_ids}
        available = {entity_id: val for entity_id, val in values.items() if val is not None}
        best_run = ""
        if available:
            if metric_preference_func(metric) == "lower":
                best_run = min(available, key=lambda entity_id: available[entity_id])
            else:
                best_run = max(available, key=lambda entity_id: available[entity_id])

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
        "subjects": subjects,
        "metrics": metric_names,
        "by_run": by_run,
        "provider_summaries_by_run": {
            str(detail.get("run_id", "")): detail.get("summary", {}).get("provider_summaries", [])
            for detail in details
        },
        "table": table,
    }
