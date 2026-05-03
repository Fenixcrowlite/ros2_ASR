#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""Build thesis-grade, schema-first benchmark artifacts from ASR run outputs."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


def _bootstrap_imports() -> Path:
    current = Path(__file__).resolve()
    project_root = current.parent.parent
    src_root = project_root / "ros2_ws" / "src"
    paths = [project_root]
    if src_root.is_dir():
        paths.extend(path for path in src_root.iterdir() if path.is_dir())
    for candidate in reversed(paths):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)
    return project_root


PROJECT_ROOT = _bootstrap_imports()

from asr_metrics.quality import normalize_text, text_quality_support  # noqa: E402


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


SCENARIOS = ("embedded", "batch", "analytics", "dialog")

SCENARIO_WEIGHTS: dict[str, dict[str, float]] = {
    "embedded": {"accuracy": 0.28, "latency": 0.27, "resources": 0.25, "robustness": 0.10, "confidence": 0.05, "deployment": 0.05},
    "batch": {"accuracy": 0.30, "latency": 0.10, "resources": 0.15, "robustness": 0.10, "confidence": 0.05, "deployment": 0.30},
    "analytics": {"accuracy": 0.45, "latency": 0.05, "resources": 0.10, "robustness": 0.20, "confidence": 0.10, "deployment": 0.10},
    "dialog": {"accuracy": 0.30, "latency": 0.25, "resources": 0.10, "robustness": 0.10, "confidence": 0.15, "deployment": 0.10},
}

FAMILY_WEIGHTS: dict[str, dict[str, float]] = {
    "accuracy": {"wer": 0.60, "cer": 0.25, "ser": 0.15},
    "latency": {"ftl_ms_p50": 0.35, "final_latency_ms_p50": 0.40, "rtf_mean": 0.25},
    "resources": {"cpu_pct_mean": 0.25, "ram_mb_peak": 0.30, "energy_j_per_audio_min": 0.30, "gpu_mem_mb_peak": 0.15},
    "robustness": {"noise_deg_pp": 0.50, "accent_gap_pp": 0.35, "oov_rate": 0.15},
    "confidence": {"ece": 0.65, "brier": 0.35},
    "deployment": {"throughput_audio_sec_per_sec": 0.40, "model_size_mb": 0.30, "cost_per_audio_hour_usd": 0.30},
}

NORMALIZATION_BOUNDS: dict[str, tuple[str, float, float]] = {
    "wer": ("lower", 0.05, 0.40),
    "cer": ("lower", 0.02, 0.25),
    "ser": ("lower", 0.05, 0.70),
    "ftl_ms_p50": ("lower", 300.0, 2000.0),
    "final_latency_ms_p50": ("lower", 500.0, 3000.0),
    "rtf_mean": ("lower", 0.50, 1.50),
    "cpu_pct_mean": ("lower", 80.0, 400.0),
    "ram_mb_peak": ("lower", 512.0, 16000.0),
    "energy_j_per_audio_min": ("lower", 200.0, 3000.0),
    "gpu_mem_mb_peak": ("lower", 0.0, 24000.0),
    "noise_deg_pp": ("lower", 0.0, 30.0),
    "accent_gap_pp": ("lower", 0.0, 30.0),
    "oov_rate": ("lower", 0.01, 0.25),
    "ece": ("lower", 0.03, 0.30),
    "brier": ("lower", 0.04, 0.30),
    "throughput_audio_sec_per_sec": ("higher", 4.0, 0.25),
    "model_size_mb": ("lower", 100.0, 10000.0),
    "cost_per_audio_hour_usd": ("lower", 0.0, 100.0),
}

UTTERANCE_FIELDS = [
    "run_id",
    "utt_id",
    "dataset",
    "split",
    "language",
    "speaker_id",
    "accent_group",
    "snr_db",
    "noise_profile",
    "backend",
    "model",
    "execution_mode",
    "ref_text",
    "hyp_text",
    "wer",
    "cer",
    "ser",
    "word_edits",
    "ref_words",
    "char_edits",
    "ref_chars",
    "ftl_ms",
    "final_latency_ms",
    "provider_compute_rtf",
    "end_to_end_rtf",
    "rtf",
    "duration_sec",
    "cpu_pct_mean",
    "cpu_pct_peak",
    "ram_mb_peak",
    "gpu_util_pct_mean",
    "gpu_mem_mb_peak",
    "energy_j",
    "confidence_mean",
    "confidence_available",
    "ece_bin",
    "correct",
    "oov_tokens",
    "oov_available",
    "oov_rate",
    "cost_usd",
    "model_size_mb",
    "trace_artifact_ref",
    "source_schema",
]

SUMMARY_FIELDS = [
    "run_id",
    "scenario",
    "backend",
    "model",
    "execution_mode",
    "dataset",
    "language",
    "num_utterances",
    "wer",
    "cer",
    "ser",
    "ftl_ms_p50",
    "ftl_ms_p95",
    "final_latency_ms_p50",
    "final_latency_ms_p95",
    "rtf_mean",
    "rtf_p95",
    "end_to_end_rtf_mean",
    "end_to_end_rtf_p95",
    "provider_compute_rtf_mean",
    "throughput_audio_sec_per_sec",
    "cpu_pct_mean",
    "cpu_pct_p95",
    "ram_mb_peak",
    "gpu_mem_mb_peak",
    "energy_j_per_audio_min",
    "ece",
    "brier",
    "confidence_available",
    "calibration_valid",
    "calibration_reason",
    "calibration_diagnostic_only",
    "noise_deg_pp",
    "accent_gap_pp",
    "oov_available",
    "oov_rate",
    "noise_metrics_available",
    "energy_available",
    "model_size_mb",
    "cost_per_audio_hour_usd",
    "scenario_score",
    "ci_95_low",
    "ci_95_high",
    "admissible",
    "admissibility_flags",
]


@dataclass(slots=True)
class LoadedPayload:
    source_kind: str
    input_path: Path
    summary: dict[str, Any]
    rows: list[dict[str, Any]]
    source_paths: dict[str, str]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


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


def _metric(row: dict[str, Any], *names: str) -> float | None:
    metrics = row.get("metrics", {})
    metric_values = metrics if isinstance(metrics, dict) else {}
    for name in names:
        value = metric_values.get(name)
        if value is None:
            value = row.get(name)
        coerced = _as_float(value)
        if coerced is not None:
            return coerced
    return None


def _percentile(values: list[float], percentile: float) -> float | None:
    ordered = sorted(value for value in values if value is not None)
    if not ordered:
        return None
    if len(ordered) == 1:
        return float(ordered[0])
    position = max(0.0, min(1.0, percentile)) * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return float(ordered[lower] + ((ordered[upper] - ordered[lower]) * weight))


def _clean_optional(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _host_ram_gb() -> float | None:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        return None
    return round((pages * page_size) / (1024**3), 2)


def _gpu_name() -> str:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return ""
    result = subprocess.run(
        [nvidia_smi, "--query-gpu=name,driver_version", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.splitlines()[0].strip() if result.stdout.strip() else ""


def _default_input(results_dir: Path) -> Path:
    candidates = [
        results_dir / "latest_benchmark_summary.json",
        results_dir / "benchmark_results.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(
        "No input was provided and no default benchmark artifacts were found. "
        f"Expected one of: {', '.join(str(item) for item in candidates)}"
    )


def _canonical_results_path(
    *,
    input_path: Path,
    summary: dict[str, Any],
    artifact_root: Path,
    results_dir: Path,
    explicit_results_json: str,
) -> Path | None:
    if explicit_results_json:
        return Path(explicit_results_json)
    if input_path.name == "summary.json" and input_path.parent.name == "reports":
        candidate = input_path.parent.parent / "metrics" / "results.json"
        if candidate.exists():
            return candidate
    run_id = str(summary.get("run_id", "") or "").strip()
    if run_id:
        candidate = artifact_root / "benchmark_runs" / run_id / "metrics" / "results.json"
        if candidate.exists():
            return candidate
    candidate = results_dir / "benchmark_results.json"
    if candidate.exists():
        return candidate
    return None


def _load_schema_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_payload(
    *,
    input_path: Path,
    artifact_root: Path,
    results_dir: Path,
    results_json: str,
) -> LoadedPayload:
    if input_path.is_dir():
        schema_csv = input_path / "utterance_metrics.csv"
        schema_summary = input_path / "summary.json"
        canonical_summary = input_path / "reports" / "summary.json"
        canonical_results = input_path / "metrics" / "results.json"
        if schema_csv.exists():
            summary = _load_json(schema_summary) if schema_summary.exists() else {}
            return LoadedPayload(
                source_kind="schema",
                input_path=input_path,
                summary=summary if isinstance(summary, dict) else {},
                rows=_load_schema_rows(schema_csv),
                source_paths={"utterance_csv": str(schema_csv), "summary_json": str(schema_summary)},
            )
        if canonical_summary.exists() and canonical_results.exists():
            summary = _load_json(canonical_summary)
            rows = _load_json(canonical_results)
            if not isinstance(summary, dict) or not isinstance(rows, list):
                raise SystemExit(f"Unsupported canonical benchmark directory: {input_path}")
            return LoadedPayload(
                source_kind="canonical",
                input_path=input_path,
                summary=summary,
                rows=[row for row in rows if isinstance(row, dict)],
                source_paths={"summary_json": str(canonical_summary), "results_json": str(canonical_results)},
            )
        raise SystemExit(f"Unsupported input directory: {input_path}")

    payload = _load_json(input_path)
    if isinstance(payload, list):
        return LoadedPayload(
            source_kind="legacy",
            input_path=input_path,
            summary={},
            rows=[row for row in payload if isinstance(row, dict)],
            source_paths={"results_json": str(input_path)},
        )
    if isinstance(payload, dict) and "provider_summaries" in payload and "run_id" in payload:
        canonical_results = _canonical_results_path(
            input_path=input_path,
            summary=payload,
            artifact_root=artifact_root,
            results_dir=results_dir,
            explicit_results_json=results_json,
        )
        if canonical_results is None or not canonical_results.exists():
            raise SystemExit(
                "Canonical summary was found, but matching results rows are missing. "
                "Pass --results-json or provide an artifacts/benchmark_runs/<run_id> directory."
            )
        rows_payload = _load_json(canonical_results)
        if not isinstance(rows_payload, list):
            raise SystemExit(f"Results JSON root must be a list: {canonical_results}")
        return LoadedPayload(
            source_kind="canonical",
            input_path=input_path,
            summary=payload,
            rows=[row for row in rows_payload if isinstance(row, dict)],
            source_paths={"summary_json": str(input_path), "results_json": str(canonical_results)},
        )
    if isinstance(payload, dict) and "manifest" in payload and "models" in payload:
        schema_csv = input_path.parent / "utterance_metrics.csv"
        if not schema_csv.exists():
            raise SystemExit(
                "Schema-first summary JSON was found, but sibling "
                f"utterance_metrics.csv is missing: {schema_csv}"
            )
        return LoadedPayload(
            source_kind="schema",
            input_path=input_path,
            summary=payload,
            rows=_load_schema_rows(schema_csv),
            source_paths={"summary_json": str(input_path), "utterance_csv": str(schema_csv)},
        )
    raise SystemExit(
        "Unsupported input schema. Expected canonical summary JSON, legacy results JSON list, "
        "canonical run directory, or schema-first run directory."
    )


def _loaded_run_id(loaded: LoadedPayload) -> str:
    run_id = str(loaded.summary.get("run_id", "") or "").strip()
    if run_id:
        return run_id
    manifest = loaded.summary.get("manifest", {})
    if isinstance(manifest, dict):
        return str(manifest.get("run_id", "") or "").strip()
    return ""


def _loaded_dataset_id(loaded: LoadedPayload) -> str:
    dataset_id = str(loaded.summary.get("dataset_id", "") or "").strip()
    if dataset_id:
        return dataset_id
    manifest = loaded.summary.get("manifest", {})
    if isinstance(manifest, dict):
        dataset = manifest.get("dataset", {})
        if isinstance(dataset, dict):
            return str(dataset.get("name", "") or "").strip()
    return ""


def _provider_label(row: dict[str, Any]) -> str:
    if "backend" in row:
        return str(row.get("backend") or "unknown")
    provider_profile = str(row.get("provider_profile", "") or "")
    provider_preset = str(row.get("provider_preset", "") or "")
    provider_id = str(row.get("provider_id", "") or "")
    if provider_profile and provider_preset:
        return f"{provider_profile}:{provider_preset}"
    return provider_profile or provider_id or "unknown"


def _model_label(row: dict[str, Any]) -> str:
    if row.get("model"):
        return str(row.get("model"))
    provider_preset = str(row.get("provider_preset", "") or "")
    if provider_preset:
        return provider_preset
    backend = str(row.get("backend", "") or "")
    if ":" in backend:
        return backend.rsplit(":", 1)[1]
    return str(row.get("provider_id", "") or "")


def _language(row: dict[str, Any]) -> str:
    if row.get("language"):
        return str(row.get("language"))
    normalized_result = row.get("normalized_result", {})
    if isinstance(normalized_result, dict):
        return str(normalized_result.get("language", "") or "")
    return ""


def _quality_support(row: dict[str, Any]) -> dict[str, Any]:
    support = row.get("quality_support", {})
    if isinstance(support, dict) and "word_edits" in support:
        return dict(support)
    reference = str(row.get("reference_text", row.get("transcript_ref", row.get("ref_text", ""))) or "")
    hypothesis = str(row.get("text", row.get("transcript_hyp", row.get("hyp_text", ""))) or "")
    return text_quality_support(reference, hypothesis).as_dict()


def _noise_profile(row: dict[str, Any]) -> str:
    if row.get("noise_profile"):
        return str(row.get("noise_profile"))
    noise_level = str(row.get("noise_level", "") or "")
    noise_mode = str(row.get("noise_mode", "") or "")
    if not noise_level and row.get("snr_db") not in (None, ""):
        return f"snr_{row.get('snr_db')}dB"
    if noise_level in {"", "clean"} and noise_mode in {"", "none"}:
        return "none"
    if noise_mode and noise_mode != "none":
        return f"{noise_mode}:{noise_level or 'unknown'}"
    return noise_level or "none"


def _load_vocabulary(path: str) -> set[str]:
    if not path:
        return set()
    vocab_path = Path(path)
    if not vocab_path.exists():
        raise SystemExit(f"Vocabulary file not found: {vocab_path}")
    tokens: set[str] = set()
    for line in vocab_path.read_text(encoding="utf-8").splitlines():
        normalized = normalize_text(line)
        tokens.update(normalized.split())
    return tokens


def _oov_counts(reference_text: str, vocabulary: set[str]) -> tuple[int, int]:
    tokens = normalize_text(reference_text).split()
    if not tokens or not vocabulary:
        return 0, len(tokens)
    return sum(1 for token in tokens if token not in vocabulary), len(tokens)


def _confidence_available(row: dict[str, Any], confidence: float | None) -> bool:
    normalized_result = row.get("normalized_result", {})
    if isinstance(normalized_result, dict) and "confidence_available" in normalized_result:
        return _as_bool(normalized_result.get("confidence_available"))
    return confidence is not None


def _execution_mode(row: dict[str, Any], *, default: str = "batch") -> str:
    value = str(row.get("execution_mode", "") or "").strip().lower()
    if value in {"batch", "streaming"}:
        return value
    return default


def _first_token_latency_ms(row: dict[str, Any], execution_mode: str) -> float | None:
    if execution_mode != "streaming":
        return None
    return _metric(row, "time_to_first_result_ms", "first_partial_latency_ms")


def _rtf_from_latency(latency_ms: float | None, duration_sec: float | None) -> float | None:
    if latency_ms is None or duration_sec is None or duration_sec <= 0.0:
        return None
    return (latency_ms / 1000.0) / duration_sec


def _normalize_rows(
    *,
    loaded: LoadedPayload,
    run_id: str,
    scenario: str,
    vocabulary: set[str],
    energy_j: float | None,
) -> list[dict[str, Any]]:
    dataset_id = _loaded_dataset_id(loaded)
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(loaded.rows, start=1):
        if loaded.source_kind == "schema" and "utt_id" in row:
            reference_text = str(row.get("ref_text", "") or "")
            hypothesis_text = str(row.get("hyp_text", "") or "")
            support = text_quality_support(reference_text, hypothesis_text).as_dict()
            confidence = _as_float(row.get("confidence_mean"))
            correct = (
                _as_bool(row.get("correct"))
                if row.get("correct") not in {"", None}
                else bool(support.get("exact_match", False))
            )
            oov_tokens, ref_tokens = _oov_counts(reference_text, vocabulary)
            execution_mode = _execution_mode(row)
            final_latency_ms = _as_float(row.get("final_latency_ms"))
            duration_sec = _as_float(row.get("duration_sec"))
            provider_compute_rtf = _as_float(row.get("provider_compute_rtf"))
            end_to_end_rtf = _as_float(row.get("end_to_end_rtf"))
            if end_to_end_rtf is None:
                end_to_end_rtf = _as_float(row.get("rtf"))
            if end_to_end_rtf is None:
                end_to_end_rtf = _rtf_from_latency(final_latency_ms, duration_sec)
            ftl_ms = _as_float(row.get("ftl_ms")) if execution_mode == "streaming" else None
            oov_available = bool(vocabulary) and ref_tokens > 0
            output_rows.append(
                {
                    **{field: row.get(field, "") for field in UTTERANCE_FIELDS},
                    "run_id": row.get("run_id") or run_id,
                    "dataset": row.get("dataset") or dataset_id,
                    "execution_mode": execution_mode,
                    "wer": _as_float(row.get("wer")) if _as_float(row.get("wer")) is not None else support["wer"],
                    "cer": _as_float(row.get("cer")) if _as_float(row.get("cer")) is not None else support["cer"],
                    "ser": _as_float(row.get("ser")) if _as_float(row.get("ser")) is not None else (0.0 if correct else 1.0),
                    "word_edits": int(support["word_edits"]),
                    "ref_words": int(support["reference_word_count"]),
                    "char_edits": int(support["char_edits"]),
                    "ref_chars": int(support["reference_char_count"]),
                    "ftl_ms": ftl_ms,
                    "final_latency_ms": final_latency_ms,
                    "provider_compute_rtf": provider_compute_rtf,
                    "end_to_end_rtf": end_to_end_rtf,
                    "rtf": end_to_end_rtf if end_to_end_rtf is not None else provider_compute_rtf,
                    "confidence_mean": confidence,
                    "confidence_available": row.get("confidence_available") or (confidence is not None),
                    "correct": correct,
                    "oov_tokens": oov_tokens,
                    "oov_available": oov_available,
                    "oov_rate": (oov_tokens / ref_tokens) if oov_available else None,
                    "source_schema": "schema",
                }
            )
            continue

        support = _quality_support(row)
        reference_text = str(row.get("reference_text", row.get("transcript_ref", "")) or "")
        hypothesis_text = str(row.get("text", row.get("transcript_hyp", "")) or "")
        confidence = _metric(row, "confidence")
        correct = bool(support.get("exact_match", False))
        duration_sec = _metric(row, "audio_duration_sec", "measured_audio_duration_sec", "duration_sec") or 0.0
        oov_tokens, ref_tokens = _oov_counts(reference_text, vocabulary)
        execution_mode = _execution_mode(row)
        ftl_ms = _first_token_latency_ms(row, execution_mode)
        final_latency_ms = _metric(row, "time_to_final_result_ms", "end_to_end_latency_ms", "total_latency_ms", "latency_ms")
        provider_compute_rtf = _metric(row, "provider_compute_rtf")
        if provider_compute_rtf is None:
            provider_compute_rtf = _rtf_from_latency(
                _metric(row, "provider_compute_latency_ms", "inference_ms"),
                duration_sec,
            )
        end_to_end_rtf = _metric(row, "end_to_end_rtf")
        if end_to_end_rtf is None:
            end_to_end_rtf = _rtf_from_latency(final_latency_ms, duration_sec)
        rtf_alias = end_to_end_rtf
        if rtf_alias is None:
            rtf_alias = provider_compute_rtf
        if rtf_alias is None:
            rtf_alias = _metric(row, "real_time_factor", "rtf")
        oov_available = bool(vocabulary) and ref_tokens > 0
        ece_bin = None
        if confidence is not None:
            ece_bin = min(int(max(0.0, min(1.0, confidence)) * 10.0), 9)
        output_rows.append(
            {
                "run_id": str(row.get("run_id", "") or run_id),
                "utt_id": str(row.get("sample_id", row.get("audio_id", row.get("request_id", f"utt_{index:04d}"))) or f"utt_{index:04d}"),
                "dataset": dataset_id or str(row.get("dataset", "") or ""),
                "split": str(row.get("split", "") or ""),
                "language": _language(row),
                "speaker_id": str(row.get("speaker_id", "") or ""),
                "accent_group": str(row.get("accent_group", "") or ""),
                "snr_db": row.get("noise_snr_db", row.get("snr_db", "")),
                "noise_profile": _noise_profile(row),
                "backend": _provider_label(row),
                "model": _model_label(row),
                "execution_mode": execution_mode,
                "ref_text": reference_text,
                "hyp_text": hypothesis_text,
                "wer": _metric(row, "wer") if _metric(row, "wer") is not None else support["wer"],
                "cer": _metric(row, "cer") if _metric(row, "cer") is not None else support["cer"],
                "ser": 0.0 if correct else 1.0,
                "word_edits": int(support.get("word_edits", 0) or 0),
                "ref_words": int(support.get("reference_word_count", 0) or 0),
                "char_edits": int(support.get("char_edits", 0) or 0),
                "ref_chars": int(support.get("reference_char_count", 0) or 0),
                "ftl_ms": ftl_ms,
                "final_latency_ms": final_latency_ms,
                "provider_compute_rtf": provider_compute_rtf,
                "end_to_end_rtf": end_to_end_rtf,
                "rtf": rtf_alias,
                "duration_sec": duration_sec,
                "cpu_pct_mean": _metric(row, "cpu_percent_mean", "cpu_percent"),
                "cpu_pct_peak": _metric(row, "cpu_percent_peak", "cpu_percent"),
                "ram_mb_peak": _metric(row, "memory_mb_peak", "ram_mb", "memory_mb"),
                "gpu_util_pct_mean": _metric(row, "gpu_util_percent_mean", "gpu_util_percent"),
                "gpu_mem_mb_peak": _metric(row, "gpu_memory_mb_peak", "gpu_mem_mb", "gpu_memory_mb"),
                "energy_j": _metric(row, "energy_j"),
                "confidence_mean": confidence,
                "confidence_available": _confidence_available(row, confidence),
                "ece_bin": ece_bin,
                "correct": correct,
                "oov_tokens": oov_tokens,
                "oov_available": oov_available,
                "oov_rate": (oov_tokens / ref_tokens) if oov_available else None,
                "cost_usd": _metric(row, "estimated_cost_usd", "cost_estimate"),
                "model_size_mb": _metric(row, "model_size_mb"),
                "trace_artifact_ref": _repo_relative_path(row.get("trace_artifact_ref", "") or ""),
                "source_schema": loaded.source_kind,
            }
        )

    if energy_j is not None and output_rows:
        total_duration = sum(float(row.get("duration_sec") or 0.0) for row in output_rows)
        if total_duration > 0.0:
            for row in output_rows:
                row["energy_j"] = energy_j * (float(row.get("duration_sec") or 0.0) / total_duration)
    return output_rows


def _sum_rate(rows: list[dict[str, Any]], edits_key: str, denom_key: str, fallback_key: str) -> float | None:
    numerator = sum(int(row.get(edits_key) or 0) for row in rows)
    denominator = sum(int(row.get(denom_key) or 0) for row in rows)
    if denominator > 0:
        return numerator / denominator
    values = [_as_float(row.get(fallback_key)) for row in rows]
    usable = [value for value in values if value is not None]
    return mean(usable) if usable else None


def _mean_optional(values: list[float | None]) -> float | None:
    usable = [value for value in values if value is not None]
    return mean(usable) if usable else None


def _max_optional(values: list[float | None]) -> float | None:
    usable = [value for value in values if value is not None]
    return max(usable) if usable else None


def _calibration(
    rows: list[dict[str, Any]], bins: int = 10
) -> tuple[float | None, float | None, int]:
    pairs = [
        (float(row["confidence_mean"]), 1.0 if _as_bool(row.get("correct")) else 0.0)
        for row in rows
        if _as_float(row.get("confidence_mean")) is not None and _as_bool(row.get("confidence_available"))
    ]
    if not pairs:
        return None, None, 0
    bucketed: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for confidence, correct in pairs:
        index = min(int(max(0.0, min(1.0, confidence)) * bins), bins - 1)
        bucketed[index].append((confidence, correct))
    total = len(pairs)
    ece = 0.0
    for bucket in bucketed:
        if not bucket:
            continue
        avg_conf = mean(confidence for confidence, _ in bucket)
        avg_acc = mean(correct for _, correct in bucket)
        ece += (len(bucket) / total) * abs(avg_acc - avg_conf)
    brier = mean((confidence - correct) ** 2 for confidence, correct in pairs)
    return ece, brier, len(pairs)


def _noise_degradation_pp(rows: list[dict[str, Any]]) -> float | None:
    clean_rows = [
        row
        for row in rows
        if str(row.get("noise_profile", "") or "") in {"", "none", "clean"}
        and row.get("snr_db") in {"", None}
    ]
    noisy_rows = [row for row in rows if row not in clean_rows]
    if not clean_rows or not noisy_rows:
        return None
    clean_wer = _sum_rate(clean_rows, "word_edits", "ref_words", "wer")
    noisy_wer = _sum_rate(noisy_rows, "word_edits", "ref_words", "wer")
    if clean_wer is None or noisy_wer is None:
        return None
    return max(0.0, (noisy_wer - clean_wer) * 100.0)


def _accent_gap_pp(rows: list[dict[str, Any]]) -> float | None:
    by_accent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        accent = str(row.get("accent_group", "") or "").strip()
        if accent:
            by_accent[accent].append(row)
    if len(by_accent) < 2:
        return None
    wers = [
        value
        for value in (_sum_rate(group_rows, "word_edits", "ref_words", "wer") for group_rows in by_accent.values())
        if value is not None
    ]
    if len(wers) < 2:
        return None
    return (max(wers) - min(wers)) * 100.0


def _bootstrap_wer_ci(rows: list[dict[str, Any]], iterations: int = 1000) -> tuple[float | None, float | None]:
    if not rows:
        return None, None
    if len(rows) == 1:
        wer = _sum_rate(rows, "word_edits", "ref_words", "wer")
        return wer, wer
    rng = random.Random(42)
    estimates: list[float] = []
    for _ in range(iterations):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        wer = _sum_rate(sample, "word_edits", "ref_words", "wer")
        if wer is not None:
            estimates.append(wer)
    if not estimates:
        return None, None
    estimates.sort()
    return _percentile(estimates, 0.025), _percentile(estimates, 0.975)


def _quality_score(metric: str, value: float | None) -> float | None:
    if value is None:
        return None
    direction, target, worst = NORMALIZATION_BOUNDS[metric]
    if direction == "lower":
        if worst == target:
            return 1.0
        score = (worst - value) / (worst - target)
    else:
        if target == worst:
            return 1.0
        score = (value - worst) / (target - worst)
    return max(0.0, min(1.0, score))


def _family_score(family: str, row: dict[str, Any]) -> float | None:
    weighted = 0.0
    used_weight = 0.0
    for metric, weight in FAMILY_WEIGHTS[family].items():
        value = _as_float(row.get(metric))
        score = _quality_score(metric, value)
        if score is None:
            continue
        weighted += weight * score
        used_weight += weight
    if used_weight <= 0.0:
        return None
    return weighted / used_weight


def _scenario_score(scenario: str, row: dict[str, Any]) -> float:
    weighted = 0.0
    used_weight = 0.0
    for family, family_weight in SCENARIO_WEIGHTS[scenario].items():
        score = _family_score(family, row)
        if score is None:
            continue
        weighted += family_weight * score
        used_weight += family_weight
    if used_weight <= 0.0:
        return 0.0
    return 100.0 * (weighted / used_weight)


def _build_summary_rows(
    *,
    rows: list[dict[str, Any]],
    run_id: str,
    scenario: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("backend", "") or "unknown"),
                str(row.get("model", "") or ""),
                str(row.get("execution_mode", "") or "batch"),
            )
        ].append(row)

    summaries: list[dict[str, Any]] = []
    for (backend, model, execution_mode), group_rows in sorted(grouped.items()):
        durations = [_as_float(row.get("duration_sec")) or 0.0 for row in group_rows]
        final_latencies = [_as_float(row.get("final_latency_ms")) for row in group_rows]
        ftl_latencies = [_as_float(row.get("ftl_ms")) for row in group_rows]
        end_to_end_rtfs = [
            _as_float(row.get("end_to_end_rtf"))
            if _as_float(row.get("end_to_end_rtf")) is not None
            else _as_float(row.get("rtf"))
            for row in group_rows
        ]
        provider_compute_rtfs = [_as_float(row.get("provider_compute_rtf")) for row in group_rows]
        cpu_values = [_as_float(row.get("cpu_pct_mean")) for row in group_rows]
        ram_peaks = [_as_float(row.get("ram_mb_peak")) for row in group_rows]
        gpu_peaks = [_as_float(row.get("gpu_mem_mb_peak")) for row in group_rows]
        energy_values = [_as_float(row.get("energy_j")) for row in group_rows]
        cost_values = [_as_float(row.get("cost_usd")) for row in group_rows]
        model_sizes = [_as_float(row.get("model_size_mb")) for row in group_rows]
        total_audio_sec = sum(durations)
        total_latency_sec = sum(value for value in (lat or 0.0 for lat in final_latencies)) / 1000.0
        total_energy = sum(value for value in energy_values if value is not None)
        energy_present = any(value is not None for value in energy_values)
        total_cost = sum(value for value in cost_values if value is not None)
        cost_present = any(value is not None for value in cost_values)
        ece, brier, confidence_count = _calibration(group_rows)
        confidence_available = confidence_count > 0
        calibration_valid = confidence_count >= 30
        calibration_reason = (
            ""
            if calibration_valid
            else "requires at least 30 confidence-bearing samples"
            if confidence_available
            else "confidence unavailable"
        )
        ci_low, ci_high = _bootstrap_wer_ci(group_rows)
        oov_tokens = sum(int(row.get("oov_tokens") or 0) for row in group_rows)
        ref_words = sum(int(row.get("ref_words") or 0) for row in group_rows)
        oov_available = any(_as_bool(row.get("oov_available")) for row in group_rows)
        noise_deg_pp = _noise_degradation_pp(group_rows)

        summary = {
            "run_id": run_id,
            "scenario": scenario,
            "backend": backend,
            "model": model,
            "execution_mode": execution_mode,
            "dataset": str(group_rows[0].get("dataset", "") or ""),
            "language": ",".join(sorted({str(row.get("language", "") or "") for row in group_rows if str(row.get("language", "") or "")})),
            "num_utterances": len(group_rows),
            "wer": _sum_rate(group_rows, "word_edits", "ref_words", "wer"),
            "cer": _sum_rate(group_rows, "char_edits", "ref_chars", "cer"),
            "ser": _mean_optional([_as_float(row.get("ser")) for row in group_rows]),
            "ftl_ms_p50": _percentile([value for value in ftl_latencies if value is not None], 0.50),
            "ftl_ms_p95": _percentile([value for value in ftl_latencies if value is not None], 0.95),
            "final_latency_ms_p50": _percentile([value for value in final_latencies if value is not None], 0.50),
            "final_latency_ms_p95": _percentile([value for value in final_latencies if value is not None], 0.95),
            "rtf_mean": _mean_optional(end_to_end_rtfs),
            "rtf_p95": _percentile([value for value in end_to_end_rtfs if value is not None], 0.95),
            "end_to_end_rtf_mean": _mean_optional(end_to_end_rtfs),
            "end_to_end_rtf_p95": _percentile([value for value in end_to_end_rtfs if value is not None], 0.95),
            "provider_compute_rtf_mean": _mean_optional(provider_compute_rtfs),
            "throughput_audio_sec_per_sec": (total_audio_sec / total_latency_sec) if total_latency_sec > 0.0 else None,
            "cpu_pct_mean": _mean_optional(cpu_values),
            "cpu_pct_p95": _percentile([value for value in cpu_values if value is not None], 0.95),
            "ram_mb_peak": _max_optional(ram_peaks),
            "gpu_mem_mb_peak": _max_optional(gpu_peaks),
            "energy_j_per_audio_min": (total_energy / (total_audio_sec / 60.0)) if energy_present and total_audio_sec > 0.0 else None,
            "ece": ece,
            "brier": brier,
            "confidence_available": confidence_available,
            "calibration_valid": calibration_valid,
            "calibration_reason": calibration_reason,
            "calibration_diagnostic_only": confidence_available and not calibration_valid,
            "noise_deg_pp": noise_deg_pp,
            "accent_gap_pp": _accent_gap_pp(group_rows),
            "oov_available": oov_available,
            "oov_rate": (oov_tokens / ref_words) if ref_words > 0 and oov_available else None,
            "noise_metrics_available": noise_deg_pp is not None,
            "energy_available": energy_present,
            "model_size_mb": _max_optional(model_sizes),
            "cost_per_audio_hour_usd": (total_cost / (total_audio_sec / 3600.0)) if cost_present and total_audio_sec > 0.0 else None,
            "ci_95_low": ci_low,
            "ci_95_high": ci_high,
        }
        summary["scenario_score"] = _scenario_score(scenario, summary)
        summaries.append(summary)

    throughputs = sorted(
        value
        for value in (_as_float(row.get("throughput_audio_sec_per_sec")) for row in summaries)
        if value is not None
    )
    batch_q25 = _percentile(throughputs, 0.25)
    baseline_wer = _analytics_baseline_wer(summaries)
    for summary in summaries:
        flags = _admissibility_flags(
            scenario=scenario,
            summary=summary,
            batch_q25=batch_q25,
            analytics_baseline_wer=baseline_wer,
        )
        summary["admissibility_flags"] = ",".join(flags)
        summary["admissible"] = not flags
    return sorted(summaries, key=lambda item: float(item.get("scenario_score") or 0.0), reverse=True)


def _analytics_baseline_wer(summaries: list[dict[str, Any]]) -> float | None:
    if not summaries:
        return None
    for summary in summaries:
        label = f"{summary.get('backend', '')}:{summary.get('model', '')}".lower()
        if "mock" in label or "baseline" in label:
            return _as_float(summary.get("wer"))
    return _as_float(sorted(summaries, key=lambda item: str(item.get("backend", "")))[0].get("wer"))


def _admissibility_flags(
    *,
    scenario: str,
    summary: dict[str, Any],
    batch_q25: float | None,
    analytics_baseline_wer: float | None,
) -> list[str]:
    flags: list[str] = []
    rtf = _as_float(summary.get("rtf_mean"))
    final_p95 = _as_float(summary.get("final_latency_ms_p95"))
    throughput = _as_float(summary.get("throughput_audio_sec_per_sec"))
    wer = _as_float(summary.get("wer"))
    ece = _as_float(summary.get("ece"))
    if scenario == "embedded" and rtf is not None and rtf > 1.0:
        flags.append("embedded_rtf_gt_1")
    if scenario == "dialog" and final_p95 is not None and final_p95 > 1500.0:
        flags.append("dialog_final_latency_p95_gt_1500_ms")
    if scenario == "dialog" and ece is None:
        flags.append("dialog_confidence_unavailable")
    if scenario == "batch" and batch_q25 is not None and throughput is not None and throughput < batch_q25:
        flags.append("batch_throughput_below_q25")
    if (
        scenario == "analytics"
        and analytics_baseline_wer is not None
        and wer is not None
        and wer > analytics_baseline_wer
    ):
        flags.append("analytics_wer_above_baseline")
    return flags


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.10g}"
    return value


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _plot_message(output_path: Path, title: str, message: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _generate_plots(summary_rows: list[dict[str, Any]], utterance_rows: list[dict[str, Any]], plots_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plots_dir.mkdir(parents=True, exist_ok=True)
    if not summary_rows:
        for name in [
            "pareto_wer_latency.png",
            "pareto_wer_energy.png",
            "latency_boxplot.png",
            "robustness_wer_by_snr.png",
            "accent_disparity.png",
            "calibration_reliability.png",
            "scenario_score.png",
        ]:
            _plot_message(plots_dir / name, name.removesuffix(".png"), "No benchmark rows available")
        return

    labels = [f"{row.get('backend', '')}:{row.get('model', '')}".strip(":") for row in summary_rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = [_as_float(row.get("wer")) or 0.0 for row in summary_rows]
    ys = [_as_float(row.get("final_latency_ms_p50")) or 0.0 for row in summary_rows]
    ax.scatter(xs, ys, color="#0f766e")
    for label, x_value, y_value in zip(labels, xs, ys, strict=False):
        ax.annotate(label, (x_value, y_value), fontsize=8)
    ax.set_xlabel("WER")
    ax.set_ylabel("Final latency p50 (ms)")
    ax.set_title("WER vs Final Latency")
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(plots_dir / "pareto_wer_latency.png")
    plt.close(fig)

    energy_pairs = [
        (label, _as_float(row.get("wer")), _as_float(row.get("energy_j_per_audio_min")))
        for label, row in zip(labels, summary_rows, strict=False)
        if _as_float(row.get("energy_j_per_audio_min")) is not None
    ]
    if energy_pairs:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.scatter([item[1] or 0.0 for item in energy_pairs], [item[2] or 0.0 for item in energy_pairs], color="#1d4ed8")
        for label, x_value, y_value in energy_pairs:
            ax.annotate(label, (x_value or 0.0, y_value or 0.0), fontsize=8)
        ax.set_xlabel("WER")
        ax.set_ylabel("Energy (J/audio-min)")
        ax.set_title("WER vs Energy")
        ax.grid(True, linestyle="--", alpha=0.35)
        fig.tight_layout()
        fig.savefig(plots_dir / "pareto_wer_energy.png")
        plt.close(fig)
    else:
        _plot_message(plots_dir / "pareto_wer_energy.png", "WER vs Energy", "Energy data unavailable")

    by_backend_latency: dict[str, list[float]] = defaultdict(list)
    for row in utterance_rows:
        latency = _as_float(row.get("final_latency_ms"))
        if latency is not None:
            by_backend_latency[str(row.get("backend", "unknown") or "unknown")].append(latency)
    if by_backend_latency:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ordered_keys = sorted(by_backend_latency)
        ax.boxplot([by_backend_latency[key] for key in ordered_keys], labels=ordered_keys)
        ax.set_ylabel("Final latency (ms)")
        ax.set_title("Latency Distribution by Backend")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        fig.tight_layout()
        fig.savefig(plots_dir / "latency_boxplot.png")
        plt.close(fig)
    else:
        _plot_message(plots_dir / "latency_boxplot.png", "Latency Distribution", "Latency data unavailable")

    snr_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in utterance_rows:
        snr = row.get("snr_db")
        label = "clean" if snr in {"", None} else f"{snr} dB"
        snr_groups[label].append(row)
    if len(snr_groups) > 1:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ordered = sorted(snr_groups, key=lambda item: 999 if item == "clean" else float(str(item).split()[0]))
        values = [(_sum_rate(snr_groups[label], "word_edits", "ref_words", "wer") or 0.0) for label in ordered]
        ax.plot(ordered, values, marker="o", color="#b45309")
        ax.set_xlabel("SNR")
        ax.set_ylabel("WER")
        ax.set_title("Robustness by SNR")
        ax.grid(True, linestyle="--", alpha=0.35)
        fig.tight_layout()
        fig.savefig(plots_dir / "robustness_wer_by_snr.png")
        plt.close(fig)
    else:
        _plot_message(plots_dir / "robustness_wer_by_snr.png", "Robustness by SNR", "No noisy/SNR split available")

    accent_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in utterance_rows:
        accent = str(row.get("accent_group", "") or "").strip()
        if accent:
            accent_groups[accent].append(row)
    if len(accent_groups) >= 2:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ordered = sorted(accent_groups)
        values = [(_sum_rate(accent_groups[label], "word_edits", "ref_words", "wer") or 0.0) for label in ordered]
        ax.bar(ordered, values, color="#0ea5e9")
        ax.set_xlabel("Accent group")
        ax.set_ylabel("WER")
        ax.set_title("Accent Disparity")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        fig.tight_layout()
        fig.savefig(plots_dir / "accent_disparity.png")
        plt.close(fig)
    else:
        _plot_message(plots_dir / "accent_disparity.png", "Accent Disparity", "Accent metadata unavailable")

    calibration_pairs = [
        (_as_float(row.get("confidence_mean")), 1.0 if _as_bool(row.get("correct")) else 0.0)
        for row in utterance_rows
        if _as_float(row.get("confidence_mean")) is not None and _as_bool(row.get("confidence_available"))
    ]
    if calibration_pairs:
        bins = list(range(10))
        acc_values: list[float] = []
        conf_values: list[float] = []
        for bin_index in bins:
            low = bin_index / 10.0
            high = (bin_index + 1) / 10.0
            bucket = [
                (confidence, correct)
                for confidence, correct in calibration_pairs
                if low <= (confidence or 0.0) < high or (bin_index == 9 and confidence == 1.0)
            ]
            acc_values.append(mean(correct for _, correct in bucket) if bucket else 0.0)
            conf_values.append(mean(confidence or 0.0 for confidence, _ in bucket) if bucket else (low + high) / 2.0)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot([0, 1], [0, 1], linestyle="--", color="#64748b", label="perfect")
        ax.plot(conf_values, acc_values, marker="o", color="#0f766e", label="observed")
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_title("Reliability Diagram")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend()
        fig.tight_layout()
        fig.savefig(plots_dir / "calibration_reliability.png")
        plt.close(fig)
    else:
        _plot_message(plots_dir / "calibration_reliability.png", "Reliability Diagram", "Confidence data unavailable")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    scores = [_as_float(row.get("scenario_score")) or 0.0 for row in summary_rows]
    colors = ["#0f766e" if _as_bool(row.get("admissible")) else "#be123c" for row in summary_rows]
    ax.bar(labels, scores, color=colors)
    ax.set_ylabel("Scenario score")
    ax.set_title("Scenario Score by Model")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(plots_dir / "scenario_score.png")
    plt.close(fig)


def _build_manifest(
    *,
    run_id: str,
    scenario: str,
    normalization_profile: str,
    loaded: LoadedPayload,
    summary_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    best = summary_rows[0] if summary_rows else {}
    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "scenario": scenario,
        "normalization_profile": normalization_profile,
        "repo": {
            "name": "ros2_ASR",
            "commit_sha": _git_value("rev-parse", "HEAD"),
            "branch": _git_value("branch", "--show-current"),
        },
        "environment": {
            "os": platform.platform(),
            "ros_distro": os.environ.get("ROS_DISTRO", ""),
            "python": platform.python_version(),
            "cpu": platform.processor() or platform.machine(),
            "ram_gb": _host_ram_gb(),
            "gpu": _gpu_name(),
        },
        "dataset": {
            "name": _loaded_dataset_id(loaded),
            "normalization_profile": normalization_profile,
            "num_utterances": sum(int(row.get("num_utterances") or 0) for row in summary_rows),
        },
        "metrics": {
            "best_backend": best.get("backend", ""),
            "best_model": best.get("model", ""),
            "best_scenario_score": best.get("scenario_score"),
            "best_wer": best.get("wer"),
            "providers": len(summary_rows),
        },
        "source": {
            "kind": loaded.source_kind,
            "input_path": _repo_relative_path(loaded.input_path),
            **{
                key: _repo_relative_path(value)
                for key, value in loaded.source_paths.items()
            },
        },
        "artifacts": {
            "manifest": _repo_relative_path(output_dir / "manifest.json"),
            "utterance_csv": _repo_relative_path(output_dir / "utterance_metrics.csv"),
            "summary_csv": _repo_relative_path(output_dir / "summary.csv"),
            "summary_json": _repo_relative_path(output_dir / "summary.json"),
            "report_md": _repo_relative_path(output_dir / "report.md"),
            "plots_dir": _repo_relative_path(output_dir / "plots"),
        },
    }


def _write_markdown_report(path: Path, manifest: dict[str, Any], summary_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# ASR Thesis Benchmark Summary",
        "",
        f"Run ID: `{manifest['run_id']}`",
        f"Scenario: `{manifest['scenario']}`",
        f"Normalization: `{manifest['normalization_profile']}`",
        "",
        "## Model Ranking",
        "",
        "| Backend | Model | WER | CER | Final p95 ms | RTF | Score | Admissible | Flags |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("backend", "")),
                    str(row.get("model", "")),
                    _csv_value(row.get("wer")),
                    _csv_value(row.get("cer")),
                    _csv_value(row.get("final_latency_ms_p95")),
                    _csv_value(row.get("rtf_mean")),
                    _csv_value(row.get("scenario_score")),
                    "yes" if _as_bool(row.get("admissible")) else "no",
                    str(row.get("admissibility_flags", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- manifest: `{manifest['artifacts']['manifest']}`",
            f"- utterance metrics: `{manifest['artifacts']['utterance_csv']}`",
            f"- summary CSV: `{manifest['artifacts']['summary_csv']}`",
            f"- plots: `{manifest['artifacts']['plots_dir']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect schema-first ASR benchmark metrics")
    parser.add_argument("--input", default="", help="Canonical summary JSON, legacy results JSON, or run directory")
    parser.add_argument("--results-json", default="", help="Explicit canonical/legacy results JSON path")
    parser.add_argument("--results-dir", default=str(PROJECT_ROOT / "results"))
    parser.add_argument("--artifact-root", default=str(PROJECT_ROOT / "artifacts"))
    parser.add_argument("--run-id", default="", help="Override output run_id")
    parser.add_argument("--scenario", choices=SCENARIOS, default="embedded")
    parser.add_argument("--normalization-profile", default="normalized-v1")
    parser.add_argument("--vocabulary-file", default="", help="Optional newline vocabulary for OOV rate")
    parser.add_argument("--energy-j", type=float, default=None, help="Optional total measured run energy in joules")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    input_path = Path(args.input) if args.input else _default_input(results_dir)
    loaded = _load_payload(
        input_path=input_path,
        artifact_root=Path(args.artifact_root),
        results_dir=results_dir,
        results_json=args.results_json,
    )
    if not loaded.rows:
        raise SystemExit(f"No benchmark rows found in input: {input_path}")

    run_id = str(args.run_id or _loaded_run_id(loaded) or "").strip()
    if not run_id:
        run_id = f"schema_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"

    vocabulary = _load_vocabulary(args.vocabulary_file)
    utterance_rows = _normalize_rows(
        loaded=loaded,
        run_id=run_id,
        scenario=args.scenario,
        vocabulary=vocabulary,
        energy_j=args.energy_j,
    )
    summary_rows = _build_summary_rows(rows=utterance_rows, run_id=run_id, scenario=args.scenario)

    output_dir = results_dir / "runs" / run_id
    plots_dir = output_dir / "plots"
    manifest = _build_manifest(
        run_id=run_id,
        scenario=args.scenario,
        normalization_profile=args.normalization_profile,
        loaded=loaded,
        summary_rows=summary_rows,
        output_dir=output_dir,
    )

    _write_csv(output_dir / "utterance_metrics.csv", UTTERANCE_FIELDS, utterance_rows)
    _write_csv(output_dir / "summary.csv", SUMMARY_FIELDS, summary_rows)
    _write_json(output_dir / "summary.json", {"manifest": manifest, "models": summary_rows})
    _write_json(output_dir / "manifest.json", manifest)
    _write_markdown_report(output_dir / "report.md", manifest, summary_rows)
    if not args.no_plots:
        _generate_plots(summary_rows, utterance_rows, plots_dir)

    latest_ref = results_dir / "latest_schema_run.json"
    _write_json(
        latest_ref,
        {
            "run_id": run_id,
            "scenario": args.scenario,
            "run_dir": _repo_relative_path(output_dir),
            "manifest": _repo_relative_path(output_dir / "manifest.json"),
            "summary_json": _repo_relative_path(output_dir / "summary.json"),
            "summary_csv": _repo_relative_path(output_dir / "summary.csv"),
            "utterance_csv": _repo_relative_path(output_dir / "utterance_metrics.csv"),
        },
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "scenario": args.scenario,
                "run_dir": _repo_relative_path(output_dir),
                "manifest": _repo_relative_path(output_dir / "manifest.json"),
                "summary_json": _repo_relative_path(output_dir / "summary.json"),
                "summary_csv": _repo_relative_path(output_dir / "summary.csv"),
                "utterance_csv": _repo_relative_path(output_dir / "utterance_metrics.csv"),
                "plots_dir": _repo_relative_path(plots_dir),
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
