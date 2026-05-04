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
                "ci_95_low": "",
                "ci_95_high": "",
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
            }
        )
    return output


def _wer_for_rows(rows: list[dict[str, Any]]) -> float | None:
    word_edits = sum(int(float(row.get("word_edits") or 0)) for row in rows)
    ref_words = sum(int(float(row.get("ref_words") or 0)) for row in rows)
    if ref_words > 0:
        return word_edits / ref_words
    values = [_as_float(row.get("wer")) for row in rows]
    usable = [value for value in values if value is not None]
    return mean(usable) if usable else None


def _sum_rate(rows: list[dict[str, Any]], edits_key: str, denom_key: str, fallback_key: str) -> float | None:
    numerator = sum(int(float(row.get(edits_key) or 0)) for row in rows)
    denominator = sum(int(float(row.get(denom_key) or 0)) for row in rows)
    if denominator > 0:
        return numerator / denominator
    values = [_as_float(row.get(fallback_key)) for row in rows]
    usable = [value for value in values if value is not None]
    return mean(usable) if usable else None


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
        output.append(
            {
                "provider": provider,
                "comparison_tier": comparison_tier,
                "model": model,
                "local_or_cloud": meta.get("local_or_cloud", ""),
                "cost_per_audio_hour_usd": row.get("cost_per_audio_hour_usd") or meta.get("cost_per_audio_hour_usd", ""),
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


def _bar_plot(path: Path, title: str, ylabel: str, rows: list[dict[str, Any]], value_key: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pairs = [
        (f"{row.get('provider', '')}:{row.get('model', '')}".strip(":"), _as_float(row.get(value_key)))
        for row in rows
    ]
    pairs = [(label, value) for label, value in pairs if value is not None]
    if not pairs:
        _plot_message(path, title, "Data unavailable")
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = [item[0] for item in pairs]
    values = [item[1] for item in pairs]
    ax.bar(labels, values, color="#0f766e")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _generate_plots(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> None:
    plots_dir = output_dir / "plots"
    try:
        _bar_plot(plots_dir / "wer_by_provider.png", "WER by Provider", "WER", tables["quality_table.csv"], "wer")
        _bar_plot(plots_dir / "cer_by_provider.png", "CER by Provider", "CER", tables["quality_table.csv"], "cer")
        _bar_plot(plots_dir / "latency_p95_by_provider.png", "Latency p95 by Provider", "ms", tables["performance_table.csv"], "final_latency_ms_p95")
        _bar_plot(plots_dir / "rtf_by_provider.png", "End-to-End RTF by Provider", "RTF", tables["performance_table.csv"], "end_to_end_rtf_mean")
        _bar_plot(plots_dir / "noise_robustness_by_provider.png", "Noise Degradation by Provider", "percentage points", tables["noise_robustness_table.csv"], "noise_deg_pp")
        _bar_plot(plots_dir / "scenario_scores.png", "Embedded Scenario Scores", "score", tables["scenario_scores.csv"], "embedded_score")
        _plot_message(plots_dir / "wer_vs_latency_pareto.png", "WER vs Latency", "Use quality_table.csv and performance_table.csv for numeric values.")
        _plot_message(plots_dir / "cost_vs_quality.png", "Cost vs Quality", "Cost data is exported when providers report measured or estimated costs.")
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
            "## Tables Summary",
            "",
        ]
    )
    for table_name, rows in tables.items():
        lines.append(f"- `{table_name}`: {len(rows)} rows")
    lines.extend(
        [
            "",
            "## Main Findings",
            "",
            "The generated CSV tables contain the provider-level quality, performance, resource, robustness, cost and scenario suitability values used for thesis interpretation.",
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
            "Use local providers for offline ROS2 experiments and cloud providers only when internet access, credentials, latency and cost are acceptable for the laboratory scenario.",
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
