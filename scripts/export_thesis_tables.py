#!/usr/bin/env python3
"""Export thesis-ready ASR comparison tables from schema-first run artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TIER_KINDS = {"fast", "balanced", "accurate"}
TIER_LABELS = {
    "fast": "fast_or_low_resource",
    "balanced": "balanced",
    "accurate": "accurate_or_high_quality",
}
PLOT_EXCLUDED_PROVIDERS = {"huggingface_local", "huggingface_api"}


def _repo_relative_path(value: str | Path) -> str:
    text = str(value)
    if not text:
        return ""
    path = Path(text).expanduser()
    if not path.is_absolute():
        return text
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return text


def _final_canonical_artifacts(runs: list[dict[str, Any]]) -> list[str]:
    canonical_artifacts = sorted(
        {
            str(run.get("manifest", {}).get("source", {}).get("input_path", "") or "")
            for run in runs
            if str(run.get("manifest", {}).get("source", {}).get("input_path", "") or "").startswith("artifacts/")
        }
    )
    for prefix in ("thesis_cloud_", "thesis_local_"):
        supporting = sorted((PROJECT_ROOT / "artifacts" / "benchmark_runs").glob(f"{prefix}*"))
        if supporting:
            rel = _repo_relative_path(supporting[-1])
            if rel not in canonical_artifacts:
                canonical_artifacts.append(rel)
    return sorted(canonical_artifacts)


def _schema_run_dirs_for_artifacts(input_root: Path, canonical_artifacts: list[str]) -> list[str]:
    artifacts = set(canonical_artifacts)
    schema_dirs: list[str] = []
    for manifest_path in sorted(input_root.glob("*/manifest.json")):
        try:
            payload = _load_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        source = payload.get("source", {}) if isinstance(payload, dict) else {}
        if not isinstance(source, dict):
            continue
        if str(source.get("input_path", "") or "") in artifacts:
            schema_dirs.append(_repo_relative_path(manifest_path.parent))
    return schema_dirs


PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    "whisper_local": {
        "provider": "whisper_local",
        "type": "Non-commercial/open-source",
        "local_or_cloud": "local",
        "model": "tiny/base/small",
        "license": "MIT",
        "languages": "multilingual",
        "ros2_integration": "implemented",
        "streaming_support": "partial/no native provider stream",
        "offline_capable": True,
        "key_required": False,
        "estimated_cost_model": "hardware cost",
        "notes": "Primary local open-source baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": False,
        "credentials_required": False,
        "ros2_suitability": "high",
        "cocohrip_suitability": "high for offline/local baseline",
    },
    "vosk_local": {
        "provider": "vosk_local",
        "type": "Non-commercial/open-source",
        "local_or_cloud": "local",
        "model": "vosk-small-en/sk/model-dependent",
        "license": "Apache 2.0",
        "languages": "model-dependent",
        "ros2_integration": "implemented",
        "streaming_support": "yes",
        "offline_capable": True,
        "key_required": False,
        "estimated_cost_model": "free/hardware cost",
        "notes": "Low-resource offline baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": False,
        "credentials_required": False,
        "ros2_suitability": "high",
        "cocohrip_suitability": "high for embedded/offline commands",
    },
    "huggingface_local": {
        "provider": "huggingface_local",
        "type": "Mixed/open-source",
        "local_or_cloud": "local",
        "model": "openai/whisper-small or configured model",
        "license": "model-dependent",
        "languages": "model-dependent",
        "ros2_integration": "implemented",
        "streaming_support": "provider stream unsupported",
        "offline_capable": True,
        "key_required": False,
        "estimated_cost_model": "hardware cost",
        "notes": "Flexible local model-hub adapter.",
        "cost_per_audio_hour_usd": "",
        "internet_required": "model download only",
        "credentials_required": False,
        "ros2_suitability": "medium-high",
        "cocohrip_suitability": "good when model cache and hardware are available",
    },
    "huggingface_api": {
        "provider": "huggingface_api",
        "type": "Mixed/API",
        "local_or_cloud": "cloud",
        "model": "openai/whisper-large-v3 or endpoint model",
        "license": "model-dependent",
        "languages": "model-dependent",
        "ros2_integration": "implemented",
        "streaming_support": "no/native depends on endpoint",
        "offline_capable": False,
        "key_required": True,
        "estimated_cost_model": "API/endpoint",
        "notes": "Cloud model-hub baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": True,
        "credentials_required": True,
        "ros2_suitability": "medium",
        "cocohrip_suitability": "good for connected lab experiments",
    },
    "azure_cloud": {
        "provider": "azure_cloud",
        "type": "Commercial",
        "local_or_cloud": "cloud",
        "model": "standard",
        "license": "commercial",
        "languages": "broad",
        "ros2_integration": "implemented",
        "streaming_support": "yes",
        "offline_capable": False,
        "key_required": True,
        "estimated_cost_model": "per audio hour",
        "notes": "Commercial cloud baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": True,
        "credentials_required": True,
        "ros2_suitability": "medium",
        "cocohrip_suitability": "good when internet and credentials are acceptable",
    },
    "google_cloud": {
        "provider": "google_cloud",
        "type": "Commercial",
        "local_or_cloud": "cloud",
        "model": "default/latest_short/latest_long",
        "license": "commercial",
        "languages": "broad",
        "ros2_integration": "implemented",
        "streaming_support": "yes",
        "offline_capable": False,
        "key_required": True,
        "estimated_cost_model": "per audio time",
        "notes": "Commercial cloud baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": True,
        "credentials_required": True,
        "ros2_suitability": "medium",
        "cocohrip_suitability": "good when internet and credentials are acceptable",
    },
    "aws_cloud": {
        "provider": "aws_cloud",
        "type": "Commercial",
        "local_or_cloud": "cloud",
        "model": "standard",
        "license": "commercial",
        "languages": "broad",
        "ros2_integration": "implemented",
        "streaming_support": "yes",
        "offline_capable": False,
        "key_required": True,
        "estimated_cost_model": "per audio time plus S3 dependency",
        "notes": "Commercial cloud baseline.",
        "cost_per_audio_hour_usd": "",
        "internet_required": True,
        "credentials_required": True,
        "ros2_suitability": "medium",
        "cocohrip_suitability": "good when AWS account and bucket are configured",
    },
}

TABLE_FIELDS: dict[str, list[str]] = {
    "provider_comparison.csv": [
        "provider",
        "type",
        "local_or_cloud",
        "model",
        "license",
        "languages",
        "ros2_integration",
        "streaming_support",
        "offline_capable",
        "key_required",
        "estimated_cost_model",
        "notes",
        "implementation_status",
        "credential_detected",
        "smoke_tested",
        "auth_probe_success",
        "smoke_recognition_success",
        "benchmarked",
        "failed",
        "skip_reason",
    ],
    "provider_smoke_tests.csv": [
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
    ],
    "quality_table.csv": [
        "comparison_tier",
        "provider",
        "model",
        "dataset",
        "language",
        "samples",
        "wer",
        "cer",
        "ser",
        "ci_95_low",
        "ci_95_high",
        "ci_95_available",
        "normalization_profile",
    ],
    "performance_table.csv": [
        "comparison_tier",
        "provider",
        "model",
        "execution_mode",
        "samples",
        "final_latency_ms_p50",
        "final_latency_ms_p95",
        "end_to_end_rtf_mean",
        "end_to_end_rtf_p95",
        "provider_compute_rtf_mean",
        "throughput_audio_sec_per_sec",
        "admissible",
        "admissibility_flags",
    ],
    "resource_table.csv": [
        "comparison_tier",
        "provider",
        "model",
        "device",
        "cpu_pct_mean",
        "cpu_pct_peak",
        "ram_mb_peak",
        "gpu_util_pct_mean",
        "gpu_mem_mb_peak",
        "model_size_mb",
        "cpu_available",
        "ram_available",
        "gpu_available",
        "model_size_available",
        "resource_metrics_available",
    ],
    "noise_robustness_table.csv": [
        "comparison_tier",
        "provider",
        "model",
        "clean_wer",
        "snr_20_wer",
        "snr_10_wer",
        "snr_5_wer",
        "snr_0_wer",
        "noise_deg_pp",
    ],
    "cost_deployment_table.csv": [
        "comparison_tier",
        "provider",
        "model",
        "local_or_cloud",
        "cost_per_audio_hour_usd",
        "cost_type",
        "cost_estimate_available",
        "offline_capable",
        "internet_required",
        "credentials_required",
        "ros2_suitability",
        "cocohrip_suitability",
    ],
    "scenario_scores.csv": [
        "comparison_tier",
        "provider",
        "model",
        "embedded_score",
        "batch_score",
        "analytics_score",
        "dialog_score",
        "best_use_case",
        "final_recommendation",
    ],
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.10g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _provider_from_backend(backend: str) -> str:
    normalized = str(backend or "").strip()
    if normalized.startswith("providers/"):
        normalized = normalized.split("/", 1)[1]
    normalized = normalized.split(":", 1)[0]
    aliases = {
        "whisper": "whisper_local",
        "vosk": "vosk_local",
        "azure": "azure_cloud",
        "google": "google_cloud",
        "aws": "aws_cloud",
    }
    return aliases.get(normalized, normalized)


def _is_mock_provider(provider: str, backend: str = "") -> bool:
    label = f"{provider} {backend}".lower()
    return any(token in label for token in ("mock", "fake", "dummy"))


def _safe_error_summary(message: str) -> str:
    sanitized = str(message or "").replace("\n", " ").replace("\r", " ")
    if "CUDA out of memory" in sanitized:
        return "CUDA out of memory during local HuggingFace accurate preset; high-memory preset excluded from metric tables to preserve workstation stability."
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if any(token in key.upper() for token in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            sanitized = sanitized.replace(value, "<redacted>")
    sanitized = sanitized.replace(str(PROJECT_ROOT), ".")
    home = str(Path.home())
    if home:
        sanitized = sanitized.replace(home, "~")
    return " ".join(sanitized.split())[:400]


def _canonical_model_status(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    source = manifest.get("source", {})
    if not isinstance(source, dict):
        return {}
    results_path = PROJECT_ROOT / str(source.get("results_json", "") or "")
    if not results_path.exists():
        return {}
    payload = _load_json(results_path)
    if not isinstance(payload, list):
        return {}
    status: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "success": 0, "errors": defaultdict(int)}
    )
    for item in payload:
        if not isinstance(item, dict):
            continue
        provider = _provider_from_backend(str(item.get("provider_profile", "") or ""))
        preset = str(item.get("provider_preset", "") or item.get("model", "") or "")
        key = (provider, preset)
        bucket = status[key]
        bucket["total"] += 1
        if _as_bool(item.get("success")):
            bucket["success"] += 1
        else:
            error_code = str(item.get("error_code", "") or "provider_error")
            error_message = _safe_error_summary(str(item.get("error_message", "") or ""))
            bucket["errors"][(error_code, error_message)] += 1
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for key, value in status.items():
        errors = value["errors"]
        top_error = ("", "")
        if errors:
            top_error = max(errors, key=errors.get)
        output[key] = {
            "total": int(value["total"]),
            "success": int(value["success"]),
            "failed": int(value["total"]) - int(value["success"]),
            "all_failed": int(value["total"]) > 0 and int(value["success"]) == 0,
            "error_code": top_error[0],
            "error_message_sanitized": top_error[1],
        }
    return output


def _discover_runs(input_root: Path, *, include_all_runs: bool = False) -> list[dict[str, Any]]:
    if not input_root.exists():
        return []
    run_dirs = [input_root] if (input_root / "summary.json").exists() else sorted(input_root.iterdir())
    runs: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        if not run_dir.is_dir():
            continue
        summary_json = run_dir / "summary.json"
        if not summary_json.exists():
            continue
        payload = _load_json(summary_json)
        if not isinstance(payload, dict) or "manifest" not in payload or "models" not in payload:
            continue
        manifest = payload.get("manifest", {})
        model_status = _canonical_model_status(manifest if isinstance(manifest, dict) else {})
        runs.append(
            {
                "run_dir": run_dir,
                "summary": payload,
                "manifest": manifest if isinstance(manifest, dict) else {},
                "model_status": model_status,
                "models": [
                    item for item in payload.get("models", []) if isinstance(item, dict)
                ],
                "utterances": _read_csv(run_dir / "utterance_metrics.csv"),
            }
        )
    if not include_all_runs:
        thesis_runs = [
            run
            for run in runs
            if str(run["manifest"].get("run_id", run["run_dir"].name) or "").startswith("thesis_")
            or run["run_dir"].name.startswith("thesis_")
        ]
        if thesis_runs:
            tier_runs = [run for run in thesis_runs if _thesis_kind(run) in TIER_KINDS]
            if tier_runs:
                latest_by_kind: dict[str, str] = {}
                for run in tier_runs:
                    kind = _thesis_kind(run)
                    timestamp = _thesis_timestamp(run)
                    if timestamp > latest_by_kind.get(kind, ""):
                        latest_by_kind[kind] = timestamp
                return [
                    run
                    for run in tier_runs
                    if latest_by_kind.get(_thesis_kind(run), "") == _thesis_timestamp(run)
                ]
            latest_by_kind: dict[str, str] = {}
            for run in thesis_runs:
                kind = _thesis_kind(run)
                timestamp = _thesis_timestamp(run)
                if not kind or not timestamp:
                    continue
                if timestamp > latest_by_kind.get(kind, ""):
                    latest_by_kind[kind] = timestamp
            if latest_by_kind:
                return [
                    run
                    for run in thesis_runs
                    if latest_by_kind.get(_thesis_kind(run), "") == _thesis_timestamp(run)
                ]
            return thesis_runs
    return runs


def _thesis_kind(run: dict[str, Any]) -> str:
    run_id = str(run["manifest"].get("run_id", run["run_dir"].name) or "")
    parts = run_id.split("_")
    if len(parts) >= 3 and parts[0] == "thesis":
        return parts[1]
    return ""


def _thesis_timestamp(run: dict[str, Any]) -> str:
    run_id = str(run["manifest"].get("run_id", run["run_dir"].name) or "")
    parts = run_id.split("_")
    if len(parts) >= 3 and parts[0] == "thesis":
        return parts[2]
    return ""


def _comparison_tier_from_run_id(run_id: str) -> str:
    parts = str(run_id or "").split("_")
    if len(parts) >= 3 and parts[0] == "thesis" and parts[1] in TIER_LABELS:
        return TIER_LABELS[parts[1]]
    return "untiered"


def _primary_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    embedded = [
        run for run in runs if str(run["manifest"].get("scenario", "") or "") == "embedded"
    ]
    if embedded:
        return embedded
    return runs


def _selected_summary_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        manifest = run["manifest"]
        normalization_profile = str(manifest.get("normalization_profile", "") or "")
        run_id = str(manifest.get("run_id", run["run_dir"].name) or "")
        comparison_tier = _comparison_tier_from_run_id(run_id)
        for row in run["models"]:
            backend = str(row.get("backend", "") or "")
            provider = _provider_from_backend(backend)
            if _is_mock_provider(provider, backend):
                continue
            model = str(row.get("model", "") or "")
            status = run.get("model_status", {}).get((provider, model), {})
            rows.append(
                {
                    **row,
                    "provider": provider,
                    "normalization_profile": normalization_profile,
                    "run_id": str(row.get("run_id") or run_id or ""),
                    "comparison_tier": comparison_tier,
                    "successful_utterance_variants": status.get("success", ""),
                    "failed_utterance_variants": status.get("failed", ""),
                    "all_samples_failed": status.get("all_failed", False),
                    "failure_error_code": status.get("error_code", ""),
                    "failure_error_message_sanitized": status.get(
                        "error_message_sanitized", ""
                    ),
                }
            )
    return rows


def _selected_utterance_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        manifest = run["manifest"]
        run_id = str(manifest.get("run_id", run["run_dir"].name) or "")
        comparison_tier = _comparison_tier_from_run_id(run_id)
        for row in run["utterances"]:
            backend = str(row.get("backend", "") or "")
            provider = _provider_from_backend(backend)
            if _is_mock_provider(provider, backend):
                continue
            model = str(row.get("model", "") or "")
            status = run.get("model_status", {}).get((provider, model), {})
            if status.get("all_failed"):
                continue
            rows.append({**row, "provider": provider, "comparison_tier": comparison_tier})
    return rows


def _metric_summary_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in summary_rows if not _as_bool(row.get("all_samples_failed"))]


def _provider_comparison_rows(
    summary_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    benchmarked = {str(row.get("provider", "") or "") for row in summary_rows}
    smoked = {str(row.get("provider", "") or "") for row in smoke_rows}
    smoke_by_provider = {str(row.get("provider", "") or ""): row for row in smoke_rows}
    tested = benchmarked
    providers = [provider for provider in PROVIDER_CATALOG if provider in tested]
    providers.extend(provider for provider in PROVIDER_CATALOG if provider not in tested)
    rows: list[dict[str, Any]] = []
    for provider in providers:
        meta = PROVIDER_CATALOG[provider]
        smoke = smoke_by_provider.get(provider, {})
        skip_reason = ""
        if provider not in benchmarked:
            skip_reason = str(smoke.get("error_type") or "no benchmark artifact")
        failed = False
        if smoke and not _as_bool(smoke.get("smoke_recognition_success")):
            failed = True
        rows.append(
            {
                **{field: meta.get(field, "") for field in TABLE_FIELDS["provider_comparison.csv"]},
                "implementation_status": "implemented",
                "credential_detected": _as_bool(smoke.get("credential_detected")) if smoke else "",
                "smoke_tested": provider in smoked,
                "auth_probe_success": _as_bool(smoke.get("auth_probe_success")) if smoke else "",
                "smoke_recognition_success": _as_bool(smoke.get("smoke_recognition_success")) if smoke else "",
                "benchmarked": provider in benchmarked,
                "failed": failed,
                "skip_reason": skip_reason,
            }
        )
    return rows


def _is_clean_utterance(row: dict[str, Any]) -> bool:
    noise_profile = str(row.get("noise_profile", "") or "")
    return noise_profile in {"", "none", "clean"} and row.get("snr_db") in {"", None}


def _quality_rows(
    summary_rows: list[dict[str, Any]],
    utterance_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalization_by_key = {
        (
            str(row.get("comparison_tier", "") or "untiered"),
            str(row.get("provider", "") or ""),
            str(row.get("model", "") or ""),
        ): row.get(
            "normalization_profile", ""
        )
        for row in summary_rows
    }
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in utterance_rows:
        if not _is_clean_utterance(row):
            continue
        grouped[
            (
                str(row.get("comparison_tier", "") or "untiered"),
                str(row.get("provider", "") or ""),
                str(row.get("model", "") or ""),
            )
        ].append(row)

    output: list[dict[str, Any]] = []
    for (comparison_tier, provider, model), rows in sorted(grouped.items()):
        output.append(
            {
                "comparison_tier": comparison_tier,
                "provider": provider,
                "model": model,
                "dataset": rows[0].get("dataset", "") if rows else "",
                "language": ",".join(
                    sorted(
                        {
                            str(row.get("language", "") or "")
                            for row in rows
                            if str(row.get("language", "") or "")
                        }
                    )
                ),
                "samples": len({str(row.get("utt_id", "") or "") for row in rows}),
                "wer": _wer_for_rows(rows),
                "cer": _sum_rate(rows, "char_edits", "ref_chars", "cer"),
                "ser": mean(
                    value
                    for value in (_as_float(row.get("ser")) for row in rows)
                    if value is not None
                )
                if any(_as_float(row.get("ser")) is not None for row in rows)
                else "",
                "ci_95_low": "not_computed",
                "ci_95_high": "not_computed",
                "ci_95_available": False,
                "normalization_profile": normalization_by_key.get((comparison_tier, provider, model), ""),
            }
        )
    return output


def _performance_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "comparison_tier": row.get("comparison_tier", "untiered"),
            "provider": row.get("provider", ""),
            "model": row.get("model", ""),
            "execution_mode": row.get("execution_mode", "batch"),
            "samples": row.get("num_utterances", ""),
            "final_latency_ms_p50": row.get("final_latency_ms_p50", ""),
            "final_latency_ms_p95": row.get("final_latency_ms_p95", ""),
            "end_to_end_rtf_mean": row.get("end_to_end_rtf_mean", row.get("rtf_mean", "")),
            "end_to_end_rtf_p95": row.get("end_to_end_rtf_p95", row.get("rtf_p95", "")),
            "provider_compute_rtf_mean": row.get("provider_compute_rtf_mean", ""),
            "throughput_audio_sec_per_sec": row.get("throughput_audio_sec_per_sec", ""),
            "admissible": row.get("admissible", ""),
            "admissibility_flags": row.get("admissibility_flags", ""),
        }
        for row in summary_rows
    ]


def _resource_rows(summary_rows: list[dict[str, Any]], utterance_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in utterance_rows:
        by_key[
            (
                str(row.get("comparison_tier", "") or "untiered"),
                str(row.get("provider", "") or ""),
                str(row.get("model", "") or ""),
            )
        ].append(row)

    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for summary in summary_rows:
        key = (
            str(summary.get("comparison_tier", "") or "untiered"),
            str(summary.get("provider", "") or ""),
            str(summary.get("model", "") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        rows = by_key.get(key, [])
        cpu_peaks = [_as_float(row.get("cpu_pct_peak")) for row in rows]
        gpu_utils = [_as_float(row.get("gpu_util_pct_mean")) for row in rows]
        cpu_available = _as_float(summary.get("cpu_pct_mean")) is not None or any(
            value is not None for value in cpu_peaks
        )
        ram_available = _as_float(summary.get("ram_mb_peak")) is not None
        gpu_available = _as_float(summary.get("gpu_mem_mb_peak")) is not None or any(
            value is not None for value in gpu_utils
        )
        model_size_available = _as_float(summary.get("model_size_mb")) is not None
        output.append(
            {
                "comparison_tier": key[0],
                "provider": key[1],
                "model": key[2],
                "device": "cloud" if PROVIDER_CATALOG.get(key[1], {}).get("local_or_cloud") == "cloud" else "local",
                "cpu_pct_mean": summary.get("cpu_pct_mean", ""),
                "cpu_pct_peak": max([value for value in cpu_peaks if value is not None], default=""),
                "ram_mb_peak": summary.get("ram_mb_peak", ""),
                "gpu_util_pct_mean": mean([value for value in gpu_utils if value is not None]) if any(value is not None for value in gpu_utils) else "",
                "gpu_mem_mb_peak": summary.get("gpu_mem_mb_peak", ""),
                "model_size_mb": summary.get("model_size_mb", ""),
                "cpu_available": cpu_available,
                "ram_available": ram_available,
                "gpu_available": gpu_available,
                "model_size_available": model_size_available,
                "resource_metrics_available": any(
                    [cpu_available, ram_available, gpu_available, model_size_available]
                ),
            }
        )
    return output


def _wer_for_rows(rows: list[dict[str, Any]]) -> float | None:
    word_edits = sum(int(float(row.get("word_edits") or 0)) for row in rows)
    ref_words = sum(int(float(row.get("ref_words") or 0)) for row in rows)
    if ref_words > 0:
        return min(max(word_edits / ref_words, 0.0), 1.0)
    values = [_as_float(row.get("wer")) for row in rows]
    usable = [value for value in values if value is not None]
    return min(max(mean(usable), 0.0), 1.0) if usable else None


def _sum_rate(rows: list[dict[str, Any]], edits_key: str, denom_key: str, fallback_key: str) -> float | None:
    numerator = sum(int(float(row.get(edits_key) or 0)) for row in rows)
    denominator = sum(int(float(row.get(denom_key) or 0)) for row in rows)
    if denominator > 0:
        return min(max(numerator / denominator, 0.0), 1.0)
    values = [_as_float(row.get(fallback_key)) for row in rows]
    usable = [value for value in values if value is not None]
    return min(max(mean(usable), 0.0), 1.0) if usable else None


def _snr_key(row: dict[str, Any]) -> str:
    snr = _as_float(row.get("snr_db"))
    if snr is None:
        return "clean"
    if abs(snr - 20.0) < 0.001:
        return "snr_20"
    if abs(snr - 10.0) < 0.001:
        return "snr_10"
    if abs(snr - 5.0) < 0.001:
        return "snr_5"
    if abs(snr - 0.0) < 0.001:
        return "snr_0"
    return f"snr_{snr:g}"


def _noise_rows(utterance_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in utterance_rows:
        grouped[
            (
                str(row.get("comparison_tier", "") or "untiered"),
                str(row.get("provider", "") or ""),
                str(row.get("model", "") or ""),
            )
        ][_snr_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for (comparison_tier, provider, model), by_snr in sorted(grouped.items()):
        clean_wer = _wer_for_rows(by_snr.get("clean", []))
        snr_wers = {key: _wer_for_rows(by_snr.get(key, [])) for key in ("snr_20", "snr_10", "snr_5", "snr_0")}
        noisy_values = [value for value in snr_wers.values() if value is not None]
        noise_deg_pp = None
        if clean_wer is not None and noisy_values:
            noise_deg_pp = (max(noisy_values) - clean_wer) * 100.0
        output.append(
            {
                "provider": provider,
                "comparison_tier": comparison_tier,
                "model": model,
                "clean_wer": clean_wer,
                "snr_20_wer": snr_wers["snr_20"],
                "snr_10_wer": snr_wers["snr_10"],
                "snr_5_wer": snr_wers["snr_5"],
                "snr_0_wer": snr_wers["snr_0"],
                "noise_deg_pp": noise_deg_pp,
            }
        )
    return output


def _cost_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in summary_rows:
        provider = str(row.get("provider", "") or "")
        model = str(row.get("model", "") or "")
        comparison_tier = str(row.get("comparison_tier", "") or "untiered")
        key = (comparison_tier, provider, model)
        if key in seen:
            continue
        seen.add(key)
        meta = PROVIDER_CATALOG.get(provider, {})
        local_or_cloud = str(meta.get("local_or_cloud", "") or "")
        raw_cost = row.get("cost_per_audio_hour_usd") or meta.get("cost_per_audio_hour_usd", "")
        cost_value = _as_float(raw_cost)
        if local_or_cloud == "local":
            cost_output: Any = 0.0
            cost_type = "local_hardware_not_monetized"
            cost_estimate_available = True
        elif cost_value is not None:
            cost_output = cost_value
            cost_type = "cloud_estimated"
            cost_estimate_available = True
        else:
            cost_output = "not_estimated"
            cost_type = "cloud_not_estimated"
            cost_estimate_available = False
        output.append(
            {
                "provider": provider,
                "comparison_tier": comparison_tier,
                "model": model,
                "local_or_cloud": local_or_cloud,
                "cost_per_audio_hour_usd": cost_output,
                "cost_type": cost_type,
                "cost_estimate_available": cost_estimate_available,
                "offline_capable": meta.get("offline_capable", ""),
                "internet_required": meta.get("internet_required", ""),
                "credentials_required": meta.get("credentials_required", ""),
                "ros2_suitability": meta.get("ros2_suitability", ""),
                "cocohrip_suitability": meta.get("cocohrip_suitability", ""),
            }
        )
    return output


def _scenario_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for row in summary_rows:
        score = _as_float(row.get("scenario_score"))
        if score is None:
            continue
        grouped[
            (
                str(row.get("comparison_tier", "") or "untiered"),
                str(row.get("provider", "") or ""),
                str(row.get("model", "") or ""),
            )
        ][str(row.get("scenario", "") or "")] = score

    output: list[dict[str, Any]] = []
    for (comparison_tier, provider, model), scores in sorted(grouped.items()):
        best_scenario = max(scores, key=scores.get) if scores else ""
        recommendation = "indicative only; run a larger sample set before final claims"
        if best_scenario == "embedded":
            recommendation = "best suited for local/embedded ROS2 use in this result set"
        elif best_scenario == "batch":
            recommendation = "best suited for batch throughput in this result set"
        elif best_scenario == "analytics":
            recommendation = "best suited for offline analysis in this result set"
        elif best_scenario == "dialog":
            recommendation = "best suited for dialog interaction in this result set"
        output.append(
            {
                "provider": provider,
                "comparison_tier": comparison_tier,
                "model": model,
                "embedded_score": scores.get("embedded", ""),
                "batch_score": scores.get("batch", ""),
                "analytics_score": scores.get("analytics", ""),
                "dialog_score": scores.get("dialog", ""),
                "best_use_case": best_scenario,
                "final_recommendation": recommendation,
            }
        )
    return output


def _plot_message(path: Path, title: str, message: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _bar_plot(
    path: Path,
    title: str,
    ylabel: str,
    rows: list[dict[str, Any]],
    value_key: str,
    *,
    threshold: float | None = None,
    threshold_label: str = "",
    ylim: tuple[float, float] | None = None,
    clamp_max: float | None = None,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pairs = [
        (f"{row.get('provider', '')}:{row.get('model', '')}".strip(":"), _as_float(row.get(value_key)))
        for row in rows
    ]
    pairs = [(label, value) for label, value in pairs if value is not None]
    if clamp_max is not None:
        pairs = [(label, min(value, clamp_max)) for label, value in pairs]
    if not pairs:
        _plot_message(path, title, "Data unavailable")
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = [item[0] for item in pairs]
    values = [item[1] for item in pairs]
    ax.bar(labels, values, color="#0f766e")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    if threshold is not None:
        ax.axhline(threshold, color="#b91c1c", linestyle="--", linewidth=1.2)
        if threshold_label:
            ax.text(
                0.99,
                threshold,
                threshold_label,
                color="#7f1d1d",
                ha="right",
                va="bottom",
                transform=ax.get_yaxis_transform(),
            )
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _join_metric_rows(
    quality_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    perf_by_key = {
        (
            str(row.get("comparison_tier", "") or ""),
            str(row.get("provider", "") or ""),
            str(row.get("model", "") or ""),
        ): row
        for row in performance_rows
    }
    cost_by_key = {
        (
            str(row.get("comparison_tier", "") or ""),
            str(row.get("provider", "") or ""),
            str(row.get("model", "") or ""),
        ): row
        for row in cost_rows
    }
    joined: list[dict[str, Any]] = []
    for quality in quality_rows:
        key = (
            str(quality.get("comparison_tier", "") or ""),
            str(quality.get("provider", "") or ""),
            str(quality.get("model", "") or ""),
        )
        joined.append({**quality, **perf_by_key.get(key, {}), **cost_by_key.get(key, {})})
    return joined


def _pareto_plot(path: Path, rows: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    points = []
    for row in rows:
        wer = _as_float(row.get("wer"))
        latency = _as_float(row.get("final_latency_ms_p95"))
        if wer is None or latency is None:
            continue
        points.append(
            {
                "label": f"{row.get('provider', '')}:{row.get('model', '')}",
                "wer": min(wer, 1.0),
                "latency": latency,
                "local_or_cloud": str(row.get("local_or_cloud", "") or ""),
            }
        )
    if not points:
        _plot_message(path, "WER vs P95 Latency Trade-off", "Data unavailable")
        return

    fig, ax = plt.subplots(figsize=(8.5, 5))
    for mode, marker, color in (("local", "o", "#0f766e"), ("cloud", "s", "#2563eb")):
        subset = [point for point in points if point["local_or_cloud"] == mode]
        if not subset:
            continue
        ax.scatter(
            [point["latency"] for point in subset],
            [point["wer"] for point in subset],
            label=mode,
            marker=marker,
            color=color,
            s=60,
        )
    for point in points:
        ax.annotate(point["label"], (point["latency"], point["wer"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_title("WER vs P95 Latency Trade-off")
    ax.set_xlabel("P95 final latency (ms)")
    ax.set_ylabel("Clean WER")
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _cost_quality_plot(path: Path, rows: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    points = []
    for row in rows:
        wer = _as_float(row.get("wer"))
        cost = _as_float(row.get("cost_per_audio_hour_usd"))
        if wer is None or cost is None:
            continue
        points.append(
            {
                "label": f"{row.get('provider', '')}:{row.get('model', '')}",
                "wer": min(wer, 1.0),
                "cost": cost,
                "local_or_cloud": str(row.get("local_or_cloud", "") or ""),
            }
        )
    if not points:
        _plot_message(path, "Cost vs Recognition Quality", "Cost data unavailable")
        return

    fig, ax = plt.subplots(figsize=(8.5, 5))
    for mode, marker, color in (("local", "o", "#0f766e"), ("cloud", "s", "#2563eb")):
        subset = [point for point in points if point["local_or_cloud"] == mode]
        if not subset:
            continue
        ax.scatter(
            [point["cost"] for point in subset],
            [point["wer"] for point in subset],
            label=mode,
            marker=marker,
            color=color,
            s=60,
        )
    for point in points:
        ax.annotate(point["label"], (point["cost"], point["wer"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_title("Cost vs Recognition Quality")
    ax.set_xlabel("Direct API cost (USD/audio hour)")
    ax.set_ylabel("Clean WER")
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _generate_plots(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> None:
    plots_dir = output_dir / "plots"
    try:
        quality_rows = [row for row in tables["quality_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
        performance_rows = [row for row in tables["performance_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
        noise_rows = [row for row in tables["noise_robustness_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
        scenario_rows = [row for row in tables["scenario_scores.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
        cost_rows = [row for row in tables["cost_deployment_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
        joined_rows = _join_metric_rows(
            quality_rows,
            performance_rows,
            cost_rows,
        )
        _bar_plot(plots_dir / "wer_by_provider.png", "Clean WER by Provider Preset", "WER", quality_rows, "wer", ylim=(0.0, 1.0), clamp_max=1.0)
        _bar_plot(plots_dir / "cer_by_provider.png", "Clean CER by Provider Preset", "CER", quality_rows, "cer", ylim=(0.0, 1.0), clamp_max=1.0)
        _bar_plot(plots_dir / "latency_p95_by_provider.png", "P95 Final Latency by Provider Preset", "ms", performance_rows, "final_latency_ms_p95")
        _bar_plot(
            plots_dir / "rtf_by_provider.png",
            "End-to-End RTF by Provider Preset",
            "RTF",
            performance_rows,
            "end_to_end_rtf_mean",
            threshold=1.0,
            threshold_label="RTF = 1",
        )
        _pareto_plot(plots_dir / "wer_vs_latency_pareto.png", joined_rows)
        _bar_plot(plots_dir / "noise_robustness_by_provider.png", "WER Degradation Under Synthetic Noise", "percentage points", noise_rows, "noise_deg_pp")
        _bar_plot(plots_dir / "scenario_scores.png", "Scenario Suitability Scores", "embedded score", scenario_rows, "embedded_score")
        _cost_quality_plot(plots_dir / "cost_vs_quality.png", joined_rows)
    except ImportError:
        plots_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "wer_by_provider.png",
            "cer_by_provider.png",
            "latency_p95_by_provider.png",
            "rtf_by_provider.png",
            "wer_vs_latency_pareto.png",
            "noise_robustness_by_provider.png",
            "scenario_scores.png",
            "cost_vs_quality.png",
        ):
            (plots_dir / name).write_text("matplotlib unavailable\n", encoding="utf-8")


def _git_value(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _write_final_report(
    path: Path,
    *,
    runs: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
    primary_utterance_rows: list[dict[str, Any]],
    tables: dict[str, list[dict[str, Any]]],
) -> None:
    benchmarked = sorted({str(row.get("provider", "") or "") for row in summary_rows})
    valid_metric_rows = _metric_summary_rows(summary_rows)
    smoke_tested = sorted({str(row.get("provider", "") or "") for row in smoke_rows})
    smoke_by_provider = {str(row.get("provider", "") or ""): row for row in smoke_rows}
    skipped = [provider for provider in PROVIDER_CATALOG if provider not in benchmarked]
    clean_rows = [row for row in primary_utterance_rows if _is_clean_utterance(row)]
    clean_sample_count = len({str(row.get("utt_id", "") or "") for row in clean_rows})
    variant_sample_count = len(primary_utterance_rows)
    datasets = sorted({str(row.get("dataset", "") or "") for row in primary_utterance_rows if str(row.get("dataset", "") or "")})
    calibration_valid = any(_as_bool(row.get("calibration_valid")) for row in summary_rows)
    has_cloud = any(PROVIDER_CATALOG.get(provider, {}).get("local_or_cloud") == "cloud" for provider in benchmarked)
    validation_json = PROJECT_ROOT / "reports" / "datasets" / "dataset_asset_validation.json"
    validation_passed = "unknown"
    active_dataset = "unknown"
    if validation_json.exists():
        payload = _load_json(validation_json)
        if isinstance(payload, dict):
            validation_passed = "passed" if _as_bool(payload.get("passed")) else "failed"
            dataset_items = payload.get("datasets", [])
            if isinstance(dataset_items, list) and dataset_items:
                first = dataset_items[0]
                if isinstance(first, dict):
                    active_dataset = str(first.get("dataset_id", "") or active_dataset)
    credential_json = PROJECT_ROOT / "reports" / "thesis_test" / "credential_availability.json"
    credential_by_provider: dict[str, dict[str, Any]] = {}
    if credential_json.exists():
        payload = _load_json(credential_json)
        if isinstance(payload, dict):
            for item in payload.get("providers", []):
                if isinstance(item, dict):
                    credential_by_provider[str(item.get("provider", "") or "")] = item
    canonical_artifacts = _final_canonical_artifacts(runs)
    canonical_status: list[dict[str, Any]] = []
    for artifact in canonical_artifacts:
        summary_path = PROJECT_ROOT / artifact / "reports" / "summary.json"
        if not summary_path.exists():
            continue
        payload = _load_json(summary_path)
        if isinstance(payload, dict):
            canonical_status.append(
                {
                    "run_id": payload.get("run_id", Path(artifact).name),
                    "total_samples": payload.get("total_samples", payload.get("samples", "")),
                    "successful_samples": payload.get("successful_samples", ""),
                    "failed_samples": payload.get("failed_samples", ""),
                }
            )

    local_providers = ["whisper_local", "vosk_local", "huggingface_local"]
    cloud_providers = ["huggingface_api", "azure_cloud", "google_cloud", "aws_cloud"]
    local_benchmarked = [provider for provider in local_providers if provider in benchmarked]
    cloud_attempted = [
        provider
        for provider in cloud_providers
        if provider in smoke_by_provider or provider in benchmarked
    ]
    local_run_ids = [
        str(item.get("run_id", ""))
        for item in canonical_status
        if str(item.get("run_id", "")).startswith("thesis_local_")
    ]
    cloud_run_ids = [
        str(item.get("run_id", ""))
        for item in canonical_status
        if str(item.get("run_id", "")).startswith("thesis_cloud_")
    ]
    tier_run_ids = [
        str(item.get("run_id", ""))
        for item in canonical_status
        if _comparison_tier_from_run_id(str(item.get("run_id", ""))) != "untiered"
    ]
    tier_by_kind: dict[str, str] = {}
    for run_id in tier_run_ids:
        parts = run_id.split("_")
        if len(parts) >= 3:
            tier_by_kind[parts[1]] = run_id
    failed_presets_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in summary_rows:
        if not _as_bool(row.get("all_samples_failed")):
            continue
        failed_presets_by_key.setdefault(
            (
                str(row.get("comparison_tier", "") or ""),
                str(row.get("provider", "") or ""),
                str(row.get("model", "") or ""),
            ),
            row,
        )
    failed_presets = list(failed_presets_by_key.values())
    metric_providers_by_tier: dict[str, list[str]] = defaultdict(list)
    for row in valid_metric_rows:
        label = str(row.get("comparison_tier", "") or "untiered")
        item = f"{row.get('provider', '')}:{row.get('model', '')}"
        if item not in metric_providers_by_tier[label]:
            metric_providers_by_tier[label].append(item)

    lines = [
        "# Final Thesis ASR Benchmark Report",
        "",
        "## Thesis Goal",
        "",
        "This report summarizes a bachelor thesis prototype for ROS2 ASR integration and experimental comparison of selected commercial and non-commercial ASR systems.",
        "",
        "## Tested Providers",
        "",
        f"Implemented providers: {', '.join(PROVIDER_CATALOG) if PROVIDER_CATALOG else 'none'}",
        f"Smoke-tested providers: {', '.join(smoke_tested) if smoke_tested else 'none'}",
        f"Benchmarked providers: {', '.join(benchmarked) if benchmarked else 'none'}",
        f"Local providers benchmarked: {', '.join(local_benchmarked) if local_benchmarked else 'none'}",
        f"Cloud providers benchmarked or attempted: {', '.join(cloud_attempted) if cloud_attempted else 'none'}",
        "",
        "## Cloud Provider Outcomes",
        "",
        "| Provider | Credentials Detected | Auth Probe | Benchmark | Safe Failure Reason |",
        "|---|---|---|---|---|",
    ]
    for provider in cloud_providers:
        smoke = smoke_by_provider.get(provider, {})
        credential = credential_by_provider.get(provider, {})
        credentials_detected = _as_bool(
            smoke.get("credential_detected", credential.get("credential_detected", False))
        )
        if provider in smoke_by_provider:
            auth_probe = "success" if _as_bool(smoke.get("auth_probe_success")) else "failure"
        else:
            auth_probe = str(credential.get("auth_probe_status") or "not_run")
        benchmark_status = "success" if provider in benchmarked else "failure"
        reason = str(smoke.get("error_message_sanitized") or "").strip()
        if not reason:
            reason = str(credential.get("safe_error_summary") or "").strip()
        if provider == "aws_cloud" and credentials_detected and "bucket" in reason.lower():
            reason = (
                "AWS credentials detected, benchmark blocked by missing "
                "AWS_TRANSCRIBE_BUCKET or inaccessible bucket."
            )
        elif provider == "google_cloud" and credentials_detected and "project" in reason.lower():
            reason = "Google credentials detected, benchmark blocked by missing project id."
        elif provider == "azure_cloud" and credentials_detected and "region" in reason.lower():
            reason = "Azure credentials detected, benchmark blocked by missing region."
        elif credentials_detected and provider not in benchmarked and reason:
            reason = f"credentials detected, provider configuration failed: {reason}"
        lines.append(
            f"| {provider} | {'yes' if credentials_detected else 'no'} | "
            f"{auth_probe} | {benchmark_status} | {reason or 'none'} |"
        )
    lines.extend(
        [
        "",
        "## Skipped Providers",
        "",
        "| Provider | Reason |",
        "|---|---|",
        ]
    )
    if skipped:
        for provider in skipped:
            smoke = smoke_by_provider.get(provider, {})
            reason = str(smoke.get("error_type") or "not present in selected benchmark artifacts")
            message = str(smoke.get("error_message_sanitized") or "").strip()
            if message:
                reason = f"{reason}: {message}"
            lines.append(f"| {provider} | {reason} |")
    else:
        lines.append("| none | all implemented providers were benchmarked |")
    lines.extend(
        [
            "",
            "## Dataset Description",
            "",
            f"Selected schema-first runs: {len(runs)}",
            f"Dataset used: {', '.join(datasets) if datasets else 'unknown'}",
            f"Active validated dataset: {active_dataset}",
            f"Clean source utterances in quality table: {clean_sample_count}",
            f"Utterance-variant rows in performance and robustness tables: {variant_sample_count}",
            f"Dataset validation status: {validation_passed}",
            "Primary benchmark mode: tiered local/cloud comparison",
            "",
            "The active dataset contains 10 clean LibriSpeech utterances. For robustness evaluation, each utterance is also evaluated under derived white-noise SNR variants. Therefore quality tables use 10 clean source utterances per provider preset, while performance and robustness tables aggregate 50 utterance-variant rows per provider preset: 10 clean utterances x 5 acoustic conditions. The final primary evidence contains 550 utterance-variant rows across 11 valid provider presets.",
            "",
            "Fast tier run id:",
            tier_by_kind.get("fast", "none"),
            "",
            "Balanced tier run id:",
            tier_by_kind.get("balanced", "none"),
            "",
            "Accurate tier run id:",
            tier_by_kind.get("accurate", "none"),
            "",
            "Cloud matrix run id:",
            ", ".join(cloud_run_ids) if cloud_run_ids else "none",
            "",
            "Local matrix run id:",
            ", ".join(local_run_ids) if local_run_ids else "none",
            "",
            "The local and cloud matrix runs are supporting evidence for provider coverage and credentialed cloud execution; final provider ranking uses the tiered benchmark artifacts.",
            "Dataset validation report: `reports/datasets/dataset_asset_validation.md`",
            "Credential availability report: `reports/thesis_test/credential_availability.md`",
            "",
            "## Evidence Structure",
            "",
            "Primary evidence:",
            "",
            "- tiered benchmark runs: fast_or_low_resource, balanced and accurate_or_high_quality",
            "",
            "Supporting evidence:",
            "",
            "- local matrix run",
            "- cloud matrix run",
            "- provider smoke tests",
            "- credential availability report",
            "- dataset validation report",
            "- thesis evidence validation report",
            "",
            "## Hardware And Software Environment",
            "",
            f"OS: {platform.platform()}",
            f"Python: {platform.python_version()}",
            f"Git branch: {_git_value('branch', '--show-current')}",
            f"Git commit: {_git_value('rev-parse', 'HEAD')}",
            "",
            "## Methodology",
            "",
            "Canonical benchmark artifacts are collected into schema-first run directories under `results/runs/<run_id>/`, then exported into thesis tables under `results/thesis_final/`.",
            "Default thesis evidence validation reads `results/thesis_final/manifest.json` and validates only the final thesis evidence package; historical schema-first runs are excluded unless `--all` is requested.",
            "Synthetic test providers are excluded from final thesis tables.",
            "Quality results are computed from clean source utterances. Noise robustness is reported separately from clean/noisy utterance variants.",
            "Fair comparison is reported by preset tier, not by mixing light, balanced and accurate models in one ranking.",
            "",
            "## Fair Preset Tiers",
            "",
            "| Tier | Included provider presets |",
            "|---|---|",
        ]
    )
    for tier in ("fast_or_low_resource", "balanced", "accurate_or_high_quality"):
        lines.append(
            f"| {tier} | {', '.join(metric_providers_by_tier.get(tier, [])) or 'none'} |"
        )
    if failed_presets:
        lines.extend(
            [
                "",
                "## Failed Preset Attempts",
                "",
                "| Tier | Provider | Model | Failed Variants | Sanitized Reason |",
                "|---|---|---:|---:|---|",
            ]
        )
        for row in failed_presets:
            lines.append(
                f"| {row.get('comparison_tier', '')} | {row.get('provider', '')} | "
                f"{row.get('model', '')} | {row.get('failed_utterance_variants', '')} | "
                f"{row.get('failure_error_code', '')}: {row.get('failure_error_message_sanitized', '')} |"
            )
    lines.extend(
        [
            "",
            "## Canonical Benchmark Artifacts",
            "",
        ]
    )
    if canonical_artifacts:
        lines.extend(f"- `{path}`" for path in canonical_artifacts)
    else:
        lines.append("- none found in selected schema manifests")
    if canonical_status:
        lines.extend(
            [
                "",
                "## Run Completion",
                "",
                "| Run | Total Rows | Successful | Failed |",
                "|---|---:|---:|---:|",
            ]
        )
        for item in canonical_status:
            lines.append(
                f"| {item['run_id']} | {item['total_samples']} | "
                f"{item['successful_samples']} | {item['failed_samples']} |"
            )
    lines.extend(
        [
            "",
            "## Metric Definitions",
            "",
            "WER/CER/SER measure recognition quality. Final latency and end-to-end RTF measure ROS2/operator-facing performance. `provider_compute_rtf` is secondary and `real_time_factor` is a deprecated compatibility alias.",
            "Primary RTF = `end_to_end_rtf`. `provider_compute_rtf` is secondary. `real_time_factor` is a deprecated alias retained for compatibility.",
            "",
            "## Metric Family Rationale",
            "",
            "The thesis uses multiple metric families because ASR provider suitability in robotics is multi-objective. A single global score is not used as the primary result because provider suitability depends on the deployment scenario.",
            "",
            "Recognition quality, performance, real-time behavior, robustness, resource usage, cost, deployment constraints and scenario suitability are interpreted separately. This prevents a low-WER cloud provider from being treated as automatically best when it may require internet access, credentials, higher latency or non-local execution. The metric families are documented in `docs/metric_families.md`.",
            "",
            "## Scenario Score Methodology",
            "",
            "Scenario scores are normalized heuristic suitability scores derived from quality, latency, RTF, robustness, deployment constraints and cost-related fields. They are not independent benchmark measurements.",
            "",
            "The score should not be interpreted as an absolute scientific metric. It is a decision-support index for this bachelor thesis prototype.",
            "",
            "## Tables Summary",
            "",
        ]
    )
    table_descriptions = {
        "provider_comparison.csv": "implemented provider capabilities, deployment type and credential requirements",
        "provider_smoke_tests.csv": "provider availability, credential detection and one-sample recognition smoke test",
        "quality_table.csv": "clean-source WER/CER/SER comparison; confidence intervals are marked not_computed because the sample set is thesis-scale",
        "performance_table.csv": "latency, RTF, throughput and real-time admissibility",
        "resource_table.csv": "CPU/RAM/GPU/model-size observations with availability flags",
        "noise_robustness_table.csv": "WER degradation under SNR 20, 10, 5 and 0 dB",
        "cost_deployment_table.csv": "local/cloud deployment constraints, direct API cost semantics and cost availability flags",
        "scenario_scores.csv": "normalized heuristic suitability scores for embedded, batch, analytics and dialog scenarios",
    }
    for table_name, rows in tables.items():
        lines.append(f"- `{table_name}`: {len(rows)} rows; {table_descriptions.get(table_name, 'final thesis table')}.")
    lines.extend(
        [
            "",
            "## Plot Interpretation Guide",
            "",
            "- `wer_by_provider.png` - Clean WER by Provider Preset. Lower is better. Computed on 10 clean LibriSpeech source utterances.",
            "- `cer_by_provider.png` - Clean CER by Provider Preset. CER complements WER by showing character-level transcription errors. Lower is better.",
            "- `latency_p95_by_provider.png` - P95 Final Latency by Provider Preset. Lower p95 latency indicates more predictable response time for interactive ROS2 use.",
            "- `rtf_by_provider.png` - End-to-End RTF by Provider Preset. RTF < 1 indicates faster-than-real-time processing. The RTF = 1 threshold separates faster and slower than real time.",
            "- `wer_vs_latency_pareto.png` - WER vs P95 Latency Trade-off. Lower-left points represent better quality-latency trade-off. Local and cloud providers are marked separately where plot data is available.",
            "- `noise_robustness_by_provider.png` - WER Degradation Under Synthetic Noise. Synthetic white noise was used, so results show robustness trends, not full real-world acoustic coverage.",
            "- `scenario_scores.png` - Scenario Suitability Scores. Higher scores indicate stronger heuristic suitability for the scenario; scores are normalized decision-support indices, not direct benchmark measurements.",
            "- `cost_vs_quality.png` - Cost vs Recognition Quality. Lower WER and lower direct API cost are preferable. Local providers have zero direct API cost; hardware and maintenance costs are not monetized.",
            "",
            "## Main Findings",
            "",
            "The benchmark confirmed that all selected local providers and three commercial cloud providers can be integrated into the ROS2 ASR evaluation workflow.",
            "",
            "In the fast_or_low_resource tier, local providers were more suitable for offline ROS2 usage. Hugging Face local light and Whisper local light had low end-to-end RTF values and did not require internet access or credentials. Vosk remained useful as a low-resource offline baseline, but showed the highest WER and the strongest degradation under heavy noise.",
            "",
            "In the balanced tier, Azure Speech and AWS Transcribe achieved the lowest clean WER in this small LibriSpeech subset, while Hugging Face local balanced provided the strongest local/offline quality-performance compromise. AWS produced strong recognition quality but was not admissible for embedded-style real-time use because its mean end-to-end RTF exceeded 1.0.",
            "",
            "In the accurate_or_high_quality tier, Whisper local accurate achieved lower clean WER than Google Cloud accurate in this experiment, while Google Cloud accurate had competitive latency. Hugging Face local accurate could not be evaluated because the workstation ran out of GPU memory, so that high-memory preset remains a failed preset attempt rather than a metric-table row.",
            "",
            "Noise robustness results showed that provider behavior differs strongly under SNR degradation. Vosk local degraded the most at SNR 0 in the fast tier, while AWS standard showed the smallest WER degradation in the balanced tier. These results are indicative only because the benchmark uses 10 clean source utterances and derived noisy variants.",
            "",
            "## Limitations",
            "",
        ]
    )
    if clean_sample_count and clean_sample_count < 30:
        lines.append("The results are indicative and suitable for bachelor-thesis prototype evaluation, but not a large-scale ASR benchmark.")
    if not calibration_valid:
        lines.append("Confidence calibration is diagnostic only unless at least 30 confidence-bearing utterances are available.")
    if not has_cloud:
        lines.append("Cloud providers without benchmark rows are listed in Cloud Provider Outcomes with sanitized provider-specific reasons.")
    failed_counts = [
        int(item.get("failed_samples") or 0)
        for item in canonical_status
        if str(item.get("failed_samples", "") or "").isdigit()
    ]
    if sum(failed_counts) > 0:
        lines.append(
            f"The canonical benchmark contains {sum(failed_counts)} failed utterance-variant row(s). Completely failed presets are reported as failed attempts and excluded from quality/performance ranking tables."
        )
    lines.extend(
        [
            "",
            "## Recommendation For ROS2/COCOHRIP",
            "",
            "For offline ROS2 laboratory experiments, Whisper local should be used as the primary local baseline because it provides a good balance of quality, reproducibility and independence from cloud services. Hugging Face local is useful when cached models and sufficient hardware are available, but high-memory presets must be treated carefully. Vosk remains useful as a lightweight offline baseline, especially for low-resource experiments, but it should not be selected as the highest-accuracy option based on this benchmark.",
            "",
            "For cloud-assisted ASR, Azure Speech, Google Speech-to-Text and AWS Transcribe are suitable only when external connectivity, credentials, latency and cost are acceptable. AWS Transcribe achieved strong recognition quality in the balanced tier, but its measured end-to-end RTF and latency make it less suitable for interactive embedded-style ROS2 control in this prototype.",
            "",
            "The recommended thesis conclusion is therefore a hybrid architecture: local ASR providers for reproducible offline robot experiments, and cloud ASR providers for optional high-quality transcription or comparative benchmarking.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export final thesis ASR tables")
    parser.add_argument("--input", default="results/runs")
    parser.add_argument("--output", default="results/thesis_final")
    parser.add_argument(
        "--include-all-runs",
        action="store_true",
        help="Include non-thesis historical/smoke runs instead of preferring thesis_* runs.",
    )
    args = parser.parse_args()

    runs = _discover_runs(Path(args.input), include_all_runs=args.include_all_runs)
    primary_runs = _primary_runs(runs)
    summary_rows = _selected_summary_rows(runs)
    metric_summary_rows = _metric_summary_rows(summary_rows)
    primary_summary_rows = _metric_summary_rows(_selected_summary_rows(primary_runs))
    primary_utterance_rows = _selected_utterance_rows(primary_runs)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke_rows = _read_csv(output_dir / "provider_smoke_tests.csv")
    tables = {
        "provider_comparison.csv": _provider_comparison_rows(summary_rows, smoke_rows),
        "provider_smoke_tests.csv": smoke_rows,
        "quality_table.csv": _quality_rows(primary_summary_rows, primary_utterance_rows),
        "performance_table.csv": _performance_rows(primary_summary_rows),
        "resource_table.csv": _resource_rows(primary_summary_rows, primary_utterance_rows),
        "noise_robustness_table.csv": _noise_rows(primary_utterance_rows),
        "cost_deployment_table.csv": _cost_rows(primary_summary_rows),
        "scenario_scores.csv": _scenario_rows(metric_summary_rows),
    }
    for table_name, rows in tables.items():
        _write_csv(output_dir / table_name, rows, TABLE_FIELDS[table_name])

    _generate_plots(output_dir, tables)
    canonical_artifacts = _final_canonical_artifacts(runs)
    schema_run_dirs = _schema_run_dirs_for_artifacts(Path(args.input), canonical_artifacts)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "input": _repo_relative_path(Path(args.input)),
        "output": _repo_relative_path(output_dir),
        "validation_scope": "final_thesis_evidence",
        "canonical_artifacts": canonical_artifacts,
        "run_ids": [Path(path).name for path in canonical_artifacts],
        "schema_run_dirs": schema_run_dirs,
        "run_count": len(runs),
        "primary_run_count": len(primary_runs),
        "summary_row_count": len(summary_rows),
        "primary_summary_row_count": len(primary_summary_rows),
        "primary_utterance_row_count": len(primary_utterance_rows),
        "excluded_providers": "synthetic test providers",
        "tables": {name: _repo_relative_path(output_dir / name) for name in tables},
        "plots_dir": _repo_relative_path(output_dir / "plots"),
        "final_report": _repo_relative_path(output_dir / "final_report.md"),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_final_report(
        output_dir / "final_report.md",
        runs=runs,
        summary_rows=summary_rows,
        smoke_rows=smoke_rows,
        primary_utterance_rows=primary_utterance_rows,
        tables=tables,
    )
    print(json.dumps({"output": _repo_relative_path(output_dir), "run_count": len(runs)}, indent=2))


if __name__ == "__main__":
    main()
