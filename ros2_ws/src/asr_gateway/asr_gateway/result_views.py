"""Helpers for benchmark result discovery and comparison views.

The gateway should not expose raw artifact-tree knowledge to the browser.
Instead, this module projects stored benchmark runs into GUI-facing read models:

- benchmark history rows
- one run detail view
- run-to-run comparison payloads

It also contains the recovery logic used when a run has partial artifacts or
when old/legacy artifacts need to be presented in a modern UI.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from asr_config import resolve_profile
from asr_datasets import DatasetRegistry, load_manifest
from asr_metrics.definitions import (
    metric_definition,
    metric_metadata as metric_metadata_from_registry,
    metric_preference as metric_preference_from_registry,
)
from asr_metrics.quality import text_quality_support
from asr_metrics.semantics import METRICS_SEMANTICS_VERSION
from asr_metrics.summary import summarize_result_rows
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


def _iso_from_mtime(path: Path) -> str:
    timestamp = _safe_mtime(path)
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def _summary_artifact_path(run_dir_path: Path) -> Path:
    return run_dir_path / "reports" / "summary.json"


def _job_state(job: Mapping[str, Any]) -> str:
    return str(job.get("state", "") or "").strip().lower()


def _job_has_summary(job: Mapping[str, Any]) -> bool:
    result = job.get("result", {})
    if not isinstance(result, Mapping):
        return False
    summary = result.get("summary", {})
    return isinstance(summary, Mapping) and bool(summary)


def _run_has_partial_artifacts(run_dir_path: Path) -> bool:
    if not run_dir_path.exists():
        return False

    candidate_paths = [
        run_dir_path / "manifest" / "run_manifest.json",
        run_dir_path / "metrics" / "results.json",
        run_dir_path / "metrics" / "results.csv",
        run_dir_path / "reports" / "summary.md",
        run_dir_path / "raw_outputs",
        run_dir_path / "normalized_outputs",
        run_dir_path / "derived_audio",
    ]
    for path in candidate_paths:
        if path.is_file():
            return True
        if path.is_dir():
            try:
                if any(path.iterdir()):
                    return True
            except OSError:
                continue
    return False


def resolved_run_state(
    *,
    run_dir_path: Path,
    summary: Mapping[str, Any] | None,
    job: Mapping[str, Any],
) -> str:
    """Resolve the user-facing run state from artifacts plus live job state.

    The action server is not the only source of truth. A benchmark may finish
    successfully and still look failed from the gateway's transient job memory
    if the HTTP request timed out or the process restarted. Stored artifacts win
    when they prove completion.
    """
    if _summary_artifact_path(run_dir_path).exists():
        return "completed"
    if _job_has_summary(job):
        return "completed"

    normalized_job_state = _job_state(job)
    if normalized_job_state in {"queued", "running"}:
        return normalized_job_state
    if _run_has_partial_artifacts(run_dir_path):
        return "interrupted"
    return normalized_job_state or ("completed" if summary else "unknown")


def resolved_run_message(
    *,
    run_dir_path: Path,
    summary: Mapping[str, Any] | None,
    job: Mapping[str, Any],
) -> str:
    del summary
    message = str(job.get("message", "") or "").strip()
    state = resolved_run_state(run_dir_path=run_dir_path, summary={}, job=job)
    normalized_job_state = _job_state(job)
    if state == "completed" and normalized_job_state in {"failed", "unknown"}:
        if "timed out" in message.lower():
            return "Recovered from stored artifacts after gateway timeout"
        return message or "Recovered from stored artifacts"
    if state == "interrupted":
        return message or "Run started but no final summary was written"
    return message


def resolved_run_completed_at(
    *,
    run_dir_path: Path,
    summary: Mapping[str, Any] | None,
    job: Mapping[str, Any],
) -> str:
    summary_map = summary if isinstance(summary, Mapping) else {}
    explicit = str(job.get("completed_at", "") or "").strip()
    if explicit:
        return explicit
    explicit = str(summary_map.get("completed_at", "") or "").strip()
    if explicit:
        return explicit
    run_manifest = {}
    try:
        run_manifest = json.loads((run_dir_path / "manifest" / "run_manifest.json").read_text(encoding="utf-8"))
    except Exception:
        run_manifest = {}
    explicit = str(run_manifest.get("completed_at", "") or "").strip()
    if explicit:
        return explicit
    state = resolved_run_state(run_dir_path=run_dir_path, summary={}, job=job)
    if state == "completed":
        return _iso_from_mtime(_summary_artifact_path(run_dir_path))
    if state == "interrupted":
        return _iso_from_mtime(run_dir_path)
    return ""


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
    """Best-effort resolution of the manifest behind a stored benchmark run.

    Runs can reference the dataset manifest directly, through config snapshots,
    through the dataset profile, or through registry entries. The browser only
    needs reference transcripts, so we probe several canonical locations rather
    than assuming one storage layout.
    """
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


def _sample_assets_by_sample(
    run_manifest: Mapping[str, Any],
    *,
    artifacts_root: Path,
    read_json: ReadJsonFn,
) -> dict[str, dict[str, str]]:
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
        str(sample.sample_id): {
            "reference_text": str(sample.transcript or ""),
            "source_audio_path": str(sample.audio_path or ""),
            "language": str(sample.language or ""),
        }
        for sample in samples
        if str(sample.sample_id or "").strip()
    }


def _enrich_result_row(
    row: Any,
    *,
    sample_assets_by_sample: Mapping[str, Mapping[str, str]],
    row_index: int,
) -> Any:
    if not isinstance(row, dict):
        return row

    enriched = dict(row)
    sample_id = str(enriched.get("sample_id", "") or "")
    reference_text = str(enriched.get("reference_text", "") or "")
    sample_assets = (
        dict(sample_assets_by_sample.get(sample_id, {}))
        if sample_id and isinstance(sample_assets_by_sample.get(sample_id, {}), Mapping)
        else {}
    )
    reference_texts_by_sample = {
        sample_key: str(sample_assets.get("reference_text", "") or "")
        for sample_key, sample_assets in sample_assets_by_sample.items()
    }
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
    source_audio_path = str(
        enriched.get("source_audio_path", "") or sample_assets.get("source_audio_path", "") or ""
    )
    if source_audio_path:
        enriched["source_audio_path"] = source_audio_path

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

    enriched["row_index"] = int(row_index)
    enriched["replay"] = {
        "row_index": int(row_index),
        "has_evaluated_audio": bool(str(enriched.get("input_audio_path", "") or "").strip()),
        "has_clean_audio": bool(source_audio_path),
    }

    return enriched


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_success_filter(value: str | None) -> bool | None:
    normalized = str(value or "").strip().lower()
    if not normalized or normalized == "all":
        return None
    if normalized in {"true", "1", "yes", "ok", "success"}:
        return True
    if normalized in {"false", "0", "no", "failed", "error"}:
        return False
    raise HTTPException(status_code=400, detail=f"Unsupported success filter: {value}")


def _normalize_noise_key(noise_mode: Any, noise_level: Any) -> str:
    normalized_level = str(noise_level or "clean").strip().lower() or "clean"
    normalized_mode = str(noise_mode or "none").strip().lower() or "none"
    if normalized_level == "clean" or normalized_mode == "none":
        return "clean"
    return f"{normalized_mode}:{normalized_level}"


def _provider_key_from_row(row: Mapping[str, Any]) -> str:
    provider_profile = str(row.get("provider_profile", "") or "").strip()
    provider_preset = str(row.get("provider_preset", "") or "").strip()
    provider_id = str(row.get("provider_id", "") or "").strip()
    base = provider_profile or provider_id or "unknown"
    return f"{base}:{provider_preset}" if provider_preset else base


def _provider_label(subject: Mapping[str, Any]) -> str:
    provider_profile = str(subject.get("provider_profile", "") or "").strip()
    provider_id = str(subject.get("provider_id", "") or "").strip()
    provider_key = str(subject.get("provider_key", "") or "").strip()
    provider_preset = str(subject.get("provider_preset", "") or "").strip()
    base = provider_profile or provider_id or provider_key or "unknown"
    return f"{base} [{provider_preset}]" if provider_preset else base


def _metric_value(subject: Mapping[str, Any], metric_name: str) -> float | None:
    sections = (
        "quality_metrics",
        "latency_metrics",
        "reliability_metrics",
        "cost_metrics",
        "cost_totals",
        "streaming_metrics",
        "resource_metrics",
        "diagnostic_metrics",
        "other_metrics",
        "mean_metrics",
    )
    for section_name in sections:
        section = subject.get(section_name, {})
        if not isinstance(section, Mapping):
            continue
        value = _coerce_float(section.get(metric_name))
        if value is not None:
            return value

    metric_statistics = subject.get("metric_statistics", {})
    if isinstance(metric_statistics, Mapping):
        statistic = metric_statistics.get(metric_name, {})
        if isinstance(statistic, Mapping):
            for key in ("value", "mean", "sum", "max", "min"):
                value = _coerce_float(statistic.get(key))
                if value is not None:
                    return value
    return None


def _metric_value_for_candidates(
    subject: Mapping[str, Any],
    metric_names: list[str] | tuple[str, ...],
) -> tuple[str, float | None]:
    for metric_name in metric_names:
        value = _metric_value(subject, metric_name)
        if value is not None:
            return metric_name, value
    return str(metric_names[0] if metric_names else ""), None


def _summary_metric_metadata(summary: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    raw = summary.get("metric_metadata", {})
    if isinstance(raw, Mapping):
        merged.update({str(key): dict(value) for key, value in raw.items() if isinstance(value, Mapping)})

    discovered_names: set[str] = set()
    for section_name in ("mean_metrics", "metric_statistics"):
        section = summary.get(section_name, {})
        if isinstance(section, Mapping):
            discovered_names.update(str(name) for name in section.keys())

    provider_summaries = summary.get("provider_summaries", [])
    if isinstance(provider_summaries, list):
        for provider_summary in provider_summaries:
            if not isinstance(provider_summary, Mapping):
                continue
            for section_name in ("mean_metrics", "metric_statistics"):
                section = provider_summary.get(section_name, {})
                if isinstance(section, Mapping):
                    discovered_names.update(str(name) for name in section.keys())

    merged.update(metric_metadata_from_registry(discovered_names))
    return merged


def _provider_noise_summaries(
    summary: Mapping[str, Any],
    metrics_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing = summary.get("provider_noise_summaries", [])
    if isinstance(existing, list) and existing:
        return [dict(item) for item in existing if isinstance(item, Mapping)]

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    provider_meta: dict[str, dict[str, str]] = {}
    for row in metrics_rows:
        provider_key = _provider_key_from_row(row)
        noise_key = _normalize_noise_key(row.get("noise_mode"), row.get("noise_level"))
        grouped[(provider_key, noise_key)].append(row)
        provider_meta.setdefault(
            provider_key,
            {
                "provider_key": provider_key,
                "provider_profile": str(row.get("provider_profile", "") or ""),
                "provider_id": str(row.get("provider_id", "") or ""),
                "provider_preset": str(row.get("provider_preset", "") or ""),
            },
        )

    summaries: list[dict[str, Any]] = []
    for (provider_key, noise_key), rows in sorted(grouped.items()):
        first_row = rows[0] if rows else {}
        summaries.append(
            {
                **provider_meta.get(provider_key, {}),
                "noise_key": noise_key,
                "noise_mode": str(first_row.get("noise_mode", "none") or "none"),
                "noise_level": str(first_row.get("noise_level", "clean") or "clean"),
                **summarize_result_rows(rows, exclude_corrupted=True),
            }
        )
    return summaries


def _provider_tradeoff_snapshot(
    summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    existing = summary.get("provider_tradeoff_snapshot", [])
    if isinstance(existing, list) and existing:
        return [dict(item) for item in existing if isinstance(item, Mapping)]

    provider_summaries = summary.get("provider_summaries", [])
    if not isinstance(provider_summaries, list):
        return []

    snapshot: list[dict[str, Any]] = []
    for provider_summary in provider_summaries:
        if not isinstance(provider_summary, Mapping):
            continue
        _, latency_ms = _metric_value_for_candidates(
            provider_summary,
            ("end_to_end_latency_ms", "time_to_final_result_ms", "total_latency_ms", "per_utterance_latency_ms"),
        )
        _, rtf = _metric_value_for_candidates(
            provider_summary,
            ("end_to_end_rtf", "real_time_factor", "provider_compute_rtf"),
        )
        snapshot.append(
            {
                "provider_key": str(provider_summary.get("provider_key", "") or ""),
                "provider_profile": str(provider_summary.get("provider_profile", "") or ""),
                "provider_id": str(provider_summary.get("provider_id", "") or ""),
                "provider_preset": str(provider_summary.get("provider_preset", "") or ""),
                "label": _provider_label(provider_summary),
                "wer": _metric_value(provider_summary, "wer"),
                "cer": _metric_value(provider_summary, "cer"),
                "sample_accuracy": _metric_value(provider_summary, "sample_accuracy"),
                "end_to_end_latency_ms": latency_ms,
                "end_to_end_rtf": rtf,
                "estimated_cost_usd": _metric_value(provider_summary, "estimated_cost_usd"),
                "success_rate": _metric_value(provider_summary, "success_rate"),
                "total_samples": int(provider_summary.get("total_samples", 0) or 0),
                "warning_samples": int(provider_summary.get("warning_samples", 0) or 0),
            }
        )
    snapshot.sort(
        key=lambda item: (
            float(item.get("wer")) if item.get("wer") is not None else float("inf"),
            float(item.get("end_to_end_latency_ms")) if item.get("end_to_end_latency_ms") is not None else float("inf"),
            float(item.get("estimated_cost_usd")) if item.get("estimated_cost_usd") is not None else float("inf"),
        )
    )
    return snapshot


def _sample_error_summary(
    summary: Mapping[str, Any],
    metrics_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    existing = summary.get("sample_error_summary", {})
    if isinstance(existing, Mapping) and existing:
        return dict(existing)

    total_rows = len(metrics_rows)
    failed_rows = sum(1 for row in metrics_rows if not bool(row.get("success")))
    noisy_rows = sum(
        1 for row in metrics_rows if _normalize_noise_key(row.get("noise_mode"), row.get("noise_level")) != "clean"
    )
    exact_match_rows = sum(1 for row in metrics_rows if (_metric_value(row, "sample_accuracy") or 0.0) >= 1.0)
    high_wer_rows = sum(1 for row in metrics_rows if (_metric_value(row, "wer") or 0.0) >= 0.25)
    high_cer_rows = sum(1 for row in metrics_rows if (_metric_value(row, "cer") or 0.0) >= 0.15)
    degraded_rows = sum(
        1
        for row in metrics_rows
        if isinstance(row.get("normalized_result", {}), Mapping)
        and bool(row.get("normalized_result", {}).get("degraded"))
    )
    error_codes = Counter(
        str(row.get("error_code", "") or "").strip()
        for row in metrics_rows
        if str(row.get("error_code", "") or "").strip()
    )
    provider_failures = Counter(
        _provider_label(row)
        for row in metrics_rows
        if not bool(row.get("success"))
    )
    return {
        "total_rows": total_rows,
        "failed_rows": failed_rows,
        "noisy_rows": noisy_rows,
        "clean_rows": total_rows - noisy_rows,
        "exact_match_rows": exact_match_rows,
        "high_wer_rows": high_wer_rows,
        "high_cer_rows": high_cer_rows,
        "degraded_rows": degraded_rows,
        "top_error_codes": [
            {"error_code": code, "count": count}
            for code, count in error_codes.most_common(6)
        ],
        "provider_failures": [
            {"provider": provider, "count": count}
            for provider, count in provider_failures.most_common(6)
        ],
        "bucket_cards": [
            {"id": "failed", "label": "Failed", "count": failed_rows, "tone": "error"},
            {"id": "high_wer", "label": "High WER", "count": high_wer_rows, "tone": "warn"},
            {"id": "high_cer", "label": "High CER", "count": high_cer_rows, "tone": "warn"},
            {"id": "degraded", "label": "Degraded", "count": degraded_rows, "tone": "warn"},
            {"id": "noisy", "label": "Noisy Inputs", "count": noisy_rows, "tone": "info"},
            {"id": "exact_match", "label": "Exact Match", "count": exact_match_rows, "tone": "ok"},
        ],
    }


def _available_analysis_sections(
    summary: Mapping[str, Any],
    *,
    provider_noise_summaries: list[dict[str, Any]],
    sample_error_summary: Mapping[str, Any],
) -> dict[str, bool]:
    existing = summary.get("available_analysis_sections", {})
    if isinstance(existing, Mapping) and existing:
        base = {str(key): bool(value) for key, value in existing.items()}
    else:
        provider_summaries = summary.get("provider_summaries", [])
        base = {
            "provider_comparison": bool(provider_summaries),
            "noise_robustness": len({item.get("noise_key", "") for item in provider_noise_summaries}) > 1,
            "sample_explorer": bool(sample_error_summary.get("total_rows")),
            "latency_breakdown": bool(provider_summaries),
            "reliability": any(
                bool(item.get("reliability_metrics"))
                for item in provider_summaries
                if isinstance(item, Mapping)
            ),
            "cost": any(
                bool(item.get("cost_metrics")) or _metric_value(item, "estimated_cost_usd") is not None
                for item in provider_summaries
                if isinstance(item, Mapping)
            ),
            "streaming": any(
                bool(item.get("streaming_metrics"))
                for item in provider_summaries
                if isinstance(item, Mapping)
            ),
            "resource": any(
                bool(item.get("resource_metrics"))
                for item in provider_summaries
                if isinstance(item, Mapping)
            ),
            "diagnostics": bool(sample_error_summary),
        }
    return base


def _build_provider_rankings(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    provider_summaries = summary.get("provider_summaries", [])
    if not isinstance(provider_summaries, list):
        return []

    ranking_specs = [
        ("wer", ("wer",)),
        ("cer", ("cer",)),
        ("sample_accuracy", ("sample_accuracy",)),
        ("end_to_end_latency_ms", ("end_to_end_latency_ms", "time_to_final_result_ms", "total_latency_ms", "per_utterance_latency_ms")),
        ("end_to_end_rtf", ("end_to_end_rtf", "real_time_factor", "provider_compute_rtf")),
        ("estimated_cost_usd", ("estimated_cost_usd",)),
        ("success_rate", ("success_rate",)),
    ]
    rankings: list[dict[str, Any]] = []
    for metric_name, candidates in ranking_specs:
        entries: list[dict[str, Any]] = []
        for provider_summary in provider_summaries:
            if not isinstance(provider_summary, Mapping):
                continue
            resolved_metric, value = _metric_value_for_candidates(provider_summary, candidates)
            if value is None:
                continue
            entries.append(
                {
                    "provider_key": str(provider_summary.get("provider_key", "") or ""),
                    "provider_profile": str(provider_summary.get("provider_profile", "") or ""),
                    "provider_id": str(provider_summary.get("provider_id", "") or ""),
                    "provider_preset": str(provider_summary.get("provider_preset", "") or ""),
                    "label": _provider_label(provider_summary),
                    "value": value,
                    "resolved_metric": resolved_metric,
                    "statistic": dict(provider_summary.get("metric_statistics", {}).get(resolved_metric, {}))
                    if isinstance(provider_summary.get("metric_statistics", {}), Mapping)
                    and isinstance(provider_summary.get("metric_statistics", {}).get(resolved_metric, {}), Mapping)
                    else {},
                }
            )

        if not entries:
            continue

        preference = metric_preference_from_registry(metric_name)
        entries.sort(key=lambda item: item["value"], reverse=preference == "higher")
        for index, entry in enumerate(entries, start=1):
            entry["rank"] = index

        definition = metric_definition(metric_name)
        rankings.append(
            {
                "metric": metric_name,
                "display_name": definition.display_name if definition is not None else metric_name,
                "unit": definition.unit if definition is not None else "",
                "preference": preference,
                "description": definition.description if definition is not None else "",
                "entries": entries,
            }
        )
    return rankings


def _build_tradeoff_points(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for item in _provider_tradeoff_snapshot(summary):
        latency = _coerce_float(item.get("end_to_end_latency_ms"))
        quality = _coerce_float(item.get("sample_accuracy"))
        if quality is None:
            wer = _coerce_float(item.get("wer"))
            quality = None if wer is None else max(0.0, 1.0 - wer)
        if latency is None or quality is None:
            continue
        points.append(
            {
                **item,
                "latency_ms": latency,
                "quality_score": quality,
                "cost_usd": _coerce_float(item.get("estimated_cost_usd")),
            }
        )
    return points


def _build_latency_breakdown(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    provider_summaries = summary.get("provider_summaries", [])
    if not isinstance(provider_summaries, list):
        return []

    breakdown: list[dict[str, Any]] = []
    for provider_summary in provider_summaries:
        if not isinstance(provider_summary, Mapping):
            continue
        preprocess = _metric_value(provider_summary, "preprocess_ms") or 0.0
        inference = _metric_value(provider_summary, "inference_ms") or 0.0
        postprocess = _metric_value(provider_summary, "postprocess_ms") or 0.0
        provider_compute = _metric_value(provider_summary, "provider_compute_latency_ms") or 0.0
        _, end_to_end = _metric_value_for_candidates(
            provider_summary,
            ("end_to_end_latency_ms", "time_to_final_result_ms", "total_latency_ms", "per_utterance_latency_ms"),
        )
        if end_to_end is None:
            continue
        stage_total = preprocess + inference + postprocess
        orchestration_overhead = max(0.0, end_to_end - max(stage_total, provider_compute))
        breakdown.append(
            {
                "provider_key": str(provider_summary.get("provider_key", "") or ""),
                "provider_profile": str(provider_summary.get("provider_profile", "") or ""),
                "provider_preset": str(provider_summary.get("provider_preset", "") or ""),
                "label": _provider_label(provider_summary),
                "preprocess_ms": preprocess,
                "inference_ms": inference,
                "postprocess_ms": postprocess,
                "provider_compute_latency_ms": provider_compute,
                "orchestration_overhead_ms": orchestration_overhead,
                "end_to_end_latency_ms": end_to_end,
            }
        )
    return breakdown


def _build_provider_noise_matrix(
    provider_noise_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for item in provider_noise_summaries:
        matrix.append(
            {
                "provider_key": str(item.get("provider_key", "") or ""),
                "provider_profile": str(item.get("provider_profile", "") or ""),
                "provider_preset": str(item.get("provider_preset", "") or ""),
                "label": _provider_label(item),
                "noise_key": str(item.get("noise_key", "") or ""),
                "noise_mode": str(item.get("noise_mode", "") or "none"),
                "noise_level": str(item.get("noise_level", "") or "clean"),
                "wer": _metric_value(item, "wer"),
                "cer": _metric_value(item, "cer"),
                "sample_accuracy": _metric_value(item, "sample_accuracy"),
                "end_to_end_latency_ms": _metric_value(item, "end_to_end_latency_ms")
                or _metric_value(item, "total_latency_ms"),
                "end_to_end_rtf": _metric_value(item, "end_to_end_rtf")
                or _metric_value(item, "real_time_factor"),
                "estimated_cost_usd": _metric_value(item, "estimated_cost_usd"),
                "successful_samples": int(item.get("successful_samples", 0) or 0),
                "failed_samples": int(item.get("failed_samples", 0) or 0),
                "total_samples": int(item.get("total_samples", 0) or 0),
            }
        )
    return matrix


def _build_analysis(summary: Mapping[str, Any], metrics_rows: list[dict[str, Any]]) -> dict[str, Any]:
    provider_noise_summaries = _provider_noise_summaries(summary, metrics_rows)
    sample_error_summary = _sample_error_summary(summary, metrics_rows)
    section_availability = _available_analysis_sections(
        summary,
        provider_noise_summaries=provider_noise_summaries,
        sample_error_summary=sample_error_summary,
    )
    return {
        "provider_rankings": _build_provider_rankings(summary),
        "tradeoff_points": _build_tradeoff_points(summary),
        "latency_breakdown": _build_latency_breakdown(summary),
        "provider_noise_matrix": _build_provider_noise_matrix(provider_noise_summaries),
        "sample_error_buckets": dict(sample_error_summary),
        "section_availability": section_availability,
    }


def _expanded_summary(summary: Mapping[str, Any], metrics_rows: list[dict[str, Any]]) -> dict[str, Any]:
    provider_noise_summaries = _provider_noise_summaries(summary, metrics_rows)
    sample_error_summary = _sample_error_summary(summary, metrics_rows)
    available_sections = _available_analysis_sections(
        summary,
        provider_noise_summaries=provider_noise_summaries,
        sample_error_summary=sample_error_summary,
    )
    return {
        **summary,
        "metric_metadata": _summary_metric_metadata(summary),
        "provider_noise_summaries": provider_noise_summaries,
        "provider_tradeoff_snapshot": _provider_tradeoff_snapshot(summary),
        "sample_error_summary": sample_error_summary,
        "available_analysis_sections": available_sections,
    }


def _available_row_filters(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "providers": sorted(
            {
                str(row.get("provider_profile", "") or row.get("provider_id", "") or "").strip()
                for row in rows
                if str(row.get("provider_profile", "") or row.get("provider_id", "") or "").strip()
            }
        ),
        "presets": sorted(
            {
                str(row.get("provider_preset", "") or "").strip()
                for row in rows
                if str(row.get("provider_preset", "") or "").strip()
            }
        ),
        "noise": sorted(
            {
                _normalize_noise_key(row.get("noise_mode"), row.get("noise_level"))
                for row in rows
            }
        ),
        "success": ["true", "false"],
    }


def run_rows_page(
    run_id: str,
    *,
    artifacts_root: Path,
    clean_name: CleanNameFn,
    read_json: ReadJsonFn,
    page: int,
    page_size: int,
    provider: str = "",
    preset: str = "",
    noise: str = "",
    success: str = "",
    search: str = "",
    sort: str = "sample_id",
    direction: str = "asc",
) -> dict[str, Any]:
    run_dir_path = run_dir(artifacts_root, run_id, clean_name=clean_name)
    if not run_dir_path.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 500:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 500")

    run_manifest = read_json(run_dir_path / "manifest" / "run_manifest.json", {})
    metrics_rows = read_json(run_dir_path / "metrics" / "results.json", [])
    if not isinstance(metrics_rows, list):
        metrics_rows = []
    sample_assets = _sample_assets_by_sample(
        run_manifest,
        artifacts_root=artifacts_root,
        read_json=read_json,
    )
    enriched_rows = [
        _enrich_result_row(row, sample_assets_by_sample=sample_assets, row_index=index)
        for index, row in enumerate(metrics_rows)
        if isinstance(row, dict)
    ]

    provider_filter = str(provider or "").strip()
    preset_filter = str(preset or "").strip()
    noise_filter = str(noise or "").strip().lower()
    search_filter = str(search or "").strip().lower()
    success_filter = _parse_success_filter(success)

    filtered_rows: list[dict[str, Any]] = []
    for row in enriched_rows:
        provider_value = str(row.get("provider_profile", "") or row.get("provider_id", "") or "").strip()
        preset_value = str(row.get("provider_preset", "") or "").strip()
        noise_value = _normalize_noise_key(row.get("noise_mode"), row.get("noise_level"))
        if provider_filter and provider_filter != provider_value:
            continue
        if preset_filter and preset_filter != preset_value:
            continue
        if noise_filter and noise_filter != noise_value:
            continue
        if success_filter is not None and bool(row.get("success")) != success_filter:
            continue
        if search_filter:
            haystack = " ".join(
                [
                    provider_value,
                    preset_value,
                    str(row.get("sample_id", "") or ""),
                    str(row.get("text", "") or ""),
                    str(row.get("reference_text", "") or ""),
                    str(row.get("error_code", "") or ""),
                ]
            ).lower()
            if search_filter not in haystack:
                continue
        filtered_rows.append(row)

    reverse = str(direction or "asc").strip().lower() == "desc"

    def row_sort_key(row: Mapping[str, Any]) -> Any:
        if sort == "provider":
            return str(row.get("provider_profile", "") or row.get("provider_id", "") or "")
        if sort == "preset":
            return str(row.get("provider_preset", "") or "")
        if sort == "noise":
            return _normalize_noise_key(row.get("noise_mode"), row.get("noise_level"))
        if sort == "success":
            return 1 if bool(row.get("success")) else 0
        if sort == "sample_id":
            return str(row.get("sample_id", "") or "")
        metric_value = _metric_value(row, sort)
        if metric_value is not None:
            return metric_value
        return str(row.get(sort, "") or "")

    filtered_rows.sort(key=row_sort_key, reverse=reverse)

    total = len(filtered_rows)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "run_id": run_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": filtered_rows[start:end],
        "available_filters": _available_row_filters(enriched_rows),
    }


def list_benchmark_history(
    *,
    artifacts_root: Path,
    read_json: ReadJsonFn,
    benchmark_jobs: Mapping[str, dict[str, Any]],
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Build compact history rows for the Results and Benchmark pages."""
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
        state = resolved_run_state(
            run_dir_path=run_dir_path,
            summary=summary if isinstance(summary, Mapping) else {},
            job=job,
        )

        rows.append(
            {
                "run_id": run_id,
                "state": state,
                "started_at": job.get(
                    "started_at",
                    run_manifest.get("started_at", run_manifest.get("created_at", "")),
                ),
                "completed_at": resolved_run_completed_at(
                    run_dir_path=run_dir_path,
                    summary=summary if isinstance(summary, Mapping) else {},
                    job=job,
                ),
                "message": resolved_run_message(
                    run_dir_path=run_dir_path,
                    summary=summary if isinstance(summary, Mapping) else {},
                    job=job,
                ),
                "benchmark_profile": run_manifest.get("benchmark_profile", ""),
                "dataset_profile": run_manifest.get("dataset_profile", ""),
                "scenario": run_manifest.get("scenario", summary.get("scenario", "")),
                "execution_mode": summary.get(
                    "execution_mode",
                    run_manifest.get("execution_mode", "batch"),
                ),
                "metrics_semantics_version": summary.get("metrics_semantics_version", 1),
                "legacy_metrics": bool(summary.get("legacy_metrics", True)),
                "mixed_semantics": bool(summary.get("mixed_semantics", False)),
                "warning_samples": int(summary.get("warning_samples", 0) or 0),
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
                "metrics_semantics_version": 1,
                "legacy_metrics": True,
                "mixed_semantics": False,
                "warning_samples": 0,
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
    """Build the detailed view model for one stored benchmark run.

    The first hundred result rows are intentionally enriched on read so the GUI
    can show reference text and quality breakdowns even when older artifacts did
    not persist every derived field explicitly.
    """
    run_dir_path = run_dir(artifacts_root, run_id, clean_name=clean_name)
    if not run_dir_path.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    run_manifest = read_json(run_dir_path / "manifest" / "run_manifest.json", {})
    summary = read_json(run_dir_path / "reports" / "summary.json", {})
    metrics_rows = read_json(run_dir_path / "metrics" / "results.json", [])
    normalized_rows = metrics_rows if isinstance(metrics_rows, list) else []
    sample_assets = _sample_assets_by_sample(
        run_manifest,
        artifacts_root=artifacts_root,
        read_json=read_json,
    )
    results_head = (
        [
            _enrich_result_row(
                row,
                sample_assets_by_sample=sample_assets,
                row_index=index,
            )
            for index, row in enumerate(normalized_rows[:100])
        ]
        if isinstance(metrics_rows, list)
        else []
    )
    results_count = len(normalized_rows)
    job = benchmark_jobs.get(run_id, {})
    state = resolved_run_state(
        run_dir_path=run_dir_path,
        summary=summary if isinstance(summary, Mapping) else {},
        job=job,
    )
    summary_map = summary if isinstance(summary, Mapping) else {}
    expanded_summary = _expanded_summary(summary_map, normalized_rows)

    return {
        "run_id": run_id,
        "state": state,
        "message": resolved_run_message(
            run_dir_path=run_dir_path,
            summary=summary_map,
            job=job,
        ),
        "run_manifest": run_manifest,
        "summary": {
            **expanded_summary,
            "metrics_semantics_version": expanded_summary.get("metrics_semantics_version", 1),
            "legacy_metrics": bool(expanded_summary.get("legacy_metrics", True)),
            "mixed_semantics": bool(expanded_summary.get("mixed_semantics", False)),
            "warning_samples": int(expanded_summary.get("warning_samples", 0) or 0),
        } if expanded_summary else {
            "metrics_semantics_version": 1,
            "legacy_metrics": True,
            "mixed_semantics": False,
            "warning_samples": 0,
        },
        "analysis": _build_analysis(expanded_summary, normalized_rows),
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
    """Compare run subjects on provider-summary metrics.

    Comparison operates on provider-level summary rows, not on mixed top-level
    aggregates, because multi-provider benchmark runs intentionally suppress a
    misleading "one blended winner" aggregate.
    """
    if not run_ids:
        raise HTTPException(status_code=400, detail="run_ids must not be empty")

    details = [detail_loader(run_id) for run_id in run_ids]
    subjects: list[dict[str, Any]] = []
    by_run: dict[str, dict[str, float]] = {}
    discovered_metric_names: set[str] = set()
    semantics_versions: set[int] = set()
    mixed_semantics = False

    for detail in details:
        result_run_id = str(detail.get("run_id", ""))
        summary = detail.get("summary", {})
        if isinstance(summary, Mapping):
            semantics_versions.add(int(summary.get("metrics_semantics_version", 1) or 1))
            mixed_semantics = mixed_semantics or bool(summary.get("mixed_semantics", False))
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
                        "metrics_semantics_version": int(
                            provider_summary.get(
                                "metrics_semantics_version",
                                summary.get("metrics_semantics_version", 1),
                            )
                            or 1
                        ),
                        "legacy_metrics": bool(
                            provider_summary.get("legacy_metrics", summary.get("legacy_metrics", True))
                        ),
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
                "metrics_semantics_version": int(summary.get("metrics_semantics_version", 1) or 1)
                if isinstance(summary, Mapping)
                else 1,
                "legacy_metrics": bool(summary.get("legacy_metrics", True))
                if isinstance(summary, Mapping)
                else True,
            }
        )
        by_run[result_run_id] = row

    metric_names = sorted(set(metrics) if metrics else discovered_metric_names)
    mixed_semantics = mixed_semantics or len(semantics_versions) > 1

    table: list[dict[str, Any]] = []
    entity_ids = [str(subject.get("entity_id", "")) for subject in subjects]
    for metric in metric_names:
        values = {entity_id: by_run.get(entity_id, {}).get(metric) for entity_id in entity_ids}
        available = {entity_id: val for entity_id, val in values.items() if val is not None}
        best_run = ""
        if available and not mixed_semantics:
            if metric_preference_func(metric) == "lower":
                best_run = min(available, key=lambda entity_id: available[entity_id])
            else:
                best_run = max(available, key=lambda entity_id: available[entity_id])

        table.append(
            {
                "metric": metric,
                "display_name": metric_definition(metric).display_name
                if metric_definition(metric) is not None
                else metric,
                "unit": metric_definition(metric).unit if metric_definition(metric) is not None else "",
                "preference": metric_preference_func(metric),
                "values": values,
                "best_run": best_run,
            }
        )

    chart_series: list[dict[str, Any]] = []
    subject_index = {
        str(subject.get("entity_id", "")): subject
        for subject in subjects
    }
    for item in table:
        metric = str(item.get("metric", "") or "")
        points = []
        available = [
            (entity_id, value)
            for entity_id, value in (item.get("values", {}) or {}).items()
            if value is not None
        ]
        available.sort(
            key=lambda pair: pair[1],
            reverse=item.get("preference") == "higher",
        )
        for rank, (entity_id, value) in enumerate(available, start=1):
            subject = subject_index.get(entity_id, {})
            points.append(
                {
                    "entity_id": entity_id,
                    "label": _provider_label(subject),
                    "run_id": str(subject.get("run_id", "") or ""),
                    "provider_profile": str(subject.get("provider_profile", "") or ""),
                    "provider_preset": str(subject.get("provider_preset", "") or ""),
                    "value": value,
                    "rank": rank,
                }
            )
        chart_series.append(
            {
                "metric": metric,
                "display_name": item.get("display_name", metric),
                "unit": item.get("unit", ""),
                "preference": item.get("preference", "higher"),
                "points": points,
            }
        )

    return {
        "run_ids": run_ids,
        "metrics_semantics_version": METRICS_SEMANTICS_VERSION,
        "mixed_semantics": mixed_semantics,
        "comparison_warning": (
            "Mixed metrics semantics detected. v1 and v2 runs are not directly comparable."
            if mixed_semantics
            else ""
        ),
        "subjects": subjects,
        "metrics": metric_names,
        "by_run": by_run,
        "chart_series": chart_series,
        "provider_summaries_by_run": {
            str(detail.get("run_id", "")): detail.get("summary", {}).get("provider_summaries", [])
            for detail in details
        },
        "table": table,
    }
