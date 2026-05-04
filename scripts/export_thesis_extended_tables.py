#!/usr/bin/env python3
"""Export extended multi-dataset thesis tables and plots."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROVIDER_META = {
    "whisper_local": {"local_or_cloud": "local", "offline_capable": True, "internet_required": False, "credentials_required": False, "ros2_suitability": "high", "cocohrip_suitability": "high for offline/local baseline"},
    "vosk_local": {"local_or_cloud": "local", "offline_capable": True, "internet_required": False, "credentials_required": False, "ros2_suitability": "high", "cocohrip_suitability": "high for lightweight offline commands"},
    "huggingface_local": {"local_or_cloud": "local", "offline_capable": True, "internet_required": "model download only", "credentials_required": False, "ros2_suitability": "medium-high", "cocohrip_suitability": "good when model cache and hardware are available"},
    "huggingface_api": {"local_or_cloud": "cloud", "offline_capable": False, "internet_required": True, "credentials_required": True, "ros2_suitability": "medium", "cocohrip_suitability": "connected lab experiments only"},
    "azure_cloud": {"local_or_cloud": "cloud", "offline_capable": False, "internet_required": True, "credentials_required": True, "ros2_suitability": "medium", "cocohrip_suitability": "good when internet and credentials are acceptable"},
    "google_cloud": {"local_or_cloud": "cloud", "offline_capable": False, "internet_required": True, "credentials_required": True, "ros2_suitability": "medium", "cocohrip_suitability": "good when internet and credentials are acceptable"},
    "aws_cloud": {"local_or_cloud": "cloud", "offline_capable": False, "internet_required": True, "credentials_required": True, "ros2_suitability": "medium", "cocohrip_suitability": "good when AWS account and bucket are configured"},
}
PLOT_EXCLUDED_PROVIDERS = {"huggingface_local", "huggingface_api"}

TABLE_FIELDS = {
    "quality_table.csv": ["provider", "model", "dataset", "language", "acoustic_profile", "samples", "wer", "cer", "ser", "exact_match_rate", "normalization_profile"],
    "performance_table.csv": ["provider", "model", "dataset", "language", "acoustic_profile", "samples", "final_latency_ms_p50", "final_latency_ms_p95", "end_to_end_rtf_mean", "end_to_end_rtf_p95", "provider_compute_rtf_mean", "throughput_audio_sec_per_sec", "admissible", "admissibility_flags"],
    "noise_robustness_table.csv": ["provider", "model", "dataset", "language", "acoustic_profile", "clean_wer", "snr_20_wer", "snr_10_wer", "snr_5_wer", "snr_0_wer", "noise_deg_pp", "robustness_rank_within_dataset"],
    "resource_table.csv": ["provider", "model", "dataset", "device", "cpu_pct_mean", "cpu_pct_peak", "ram_mb_peak", "gpu_util_pct_mean", "gpu_mem_mb_peak", "model_size_mb", "resource_metrics_available", "note_for_cloud_client_side_only"],
    "cost_deployment_table.csv": ["provider", "model", "local_or_cloud", "dataset_count", "total_audio_duration_sec", "estimated_cost_usd", "cost_per_audio_hour_usd", "cost_type", "offline_capable", "internet_required", "credentials_required", "ros2_suitability", "cocohrip_suitability"],
    "scenario_scores.csv": ["provider", "model", "dataset_scope", "embedded_score", "batch_score", "analytics_score", "dialog_score", "best_use_case", "final_recommendation"],
    "domain_generalization_table.csv": ["provider", "model", "language", "acoustic_profile", "dataset", "wer", "wer_delta_vs_clean_librispeech", "latency_delta_vs_clean_librispeech", "rtf_delta_vs_clean_librispeech", "domain_robustness_note"],
    "reliability_table.csv": ["provider", "model", "dataset", "language", "acoustic_profile", "total_attempts", "successful_attempts", "failed_attempts", "success_rate", "timeout_count", "rate_limit_count", "auth_error_count", "provider_error_count", "oom_count", "sanitized_error_summary"],
    "provider_dataset_matrix.csv": ["provider", "model", "dataset", "language", "acoustic_profile", "wer", "rtf_mean", "latency_p95", "success_rate", "benchmark_status"],
    "provider_language_matrix.csv": ["provider", "model", "language", "datasets", "total_samples", "wer_mean", "cer_mean", "rtf_mean", "latency_p95", "success_rate"],
    "provider_domain_matrix.csv": ["provider", "model", "acoustic_profile", "datasets", "total_samples", "wer_mean", "cer_mean", "rtf_mean", "latency_p95", "success_rate"],
}


def _repo(path: str | Path) -> str:
    p = Path(path)
    if not p.is_absolute():
        return str(path)
    try:
        return str(p.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _f(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def _provider(raw: str) -> str:
    value = str(raw or "").replace("providers/", "")
    aliases = {"whisper": "whisper_local", "vosk": "vosk_local", "azure": "azure_cloud", "google": "google_cloud", "aws": "aws_cloud"}
    return aliases.get(value, value)


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return value


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _load_registry() -> dict[str, dict[str, Any]]:
    payload = _load_json(PROJECT_ROOT / "datasets" / "registry" / "datasets_extended.json")
    output: dict[str, dict[str, Any]] = {}
    for item in payload.get("datasets", []):
        if isinstance(item, dict):
            output[str(item.get("dataset_id", ""))] = item
    return output


def _artifact_dirs(input_root: Path) -> list[Path]:
    return sorted(path for path in input_root.glob("thesis_ext_*") if (path / "metrics" / "results.json").exists())


def _rows(input_root: Path, registry: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    artifacts: list[str] = []
    for run_dir in _artifact_dirs(input_root):
        artifacts.append(_repo(run_dir))
        summary = _load_json(run_dir / "reports" / "summary.json")
        dataset_id = str(summary.get("dataset_id", "") or "")
        dataset = registry.get(dataset_id, {})
        meta = dataset.get("metadata", {}) if isinstance(dataset.get("metadata"), dict) else {}
        for row in _load_json(run_dir / "metrics" / "results.json"):
            if not isinstance(row, dict):
                continue
            provider = _provider(str(row.get("provider_profile", "") or row.get("provider_id", "")))
            model = str(row.get("provider_preset", "") or "default")
            label = f"{provider} {model}".lower()
            if any(token in label for token in ("mock", "fake", "dummy")):
                continue
            metrics = row.get("metrics", {}) if isinstance(row.get("metrics"), dict) else {}
            support = row.get("quality_support", {}) if isinstance(row.get("quality_support"), dict) else {}
            rows.append(
                {
                    **row,
                    "run_dir": _repo(run_dir),
                    "provider": provider,
                    "model": model,
                    "dataset": dataset_id,
                    "language": str(row.get("normalized_result", {}).get("language", "") if isinstance(row.get("normalized_result"), dict) else "") or str(meta.get("language", "")),
                    "acoustic_profile": str(meta.get("acoustic_profile", "")),
                    "metrics": metrics,
                    "quality_support": support,
                    "success": bool(row.get("success")),
                    "noise_key": _noise_key(row),
                    "word_edits": support.get("word_edits"),
                    "ref_words": support.get("reference_word_count"),
                    "char_edits": support.get("char_edits"),
                    "ref_chars": support.get("reference_char_count"),
                    "exact_match": bool(support.get("exact_match")),
                }
            )
    return rows, artifacts


def _noise_key(row: dict[str, Any]) -> str:
    snr = _f(row.get("noise_snr_db"))
    if snr is None:
        return "clean"
    if abs(snr - 20) < 0.01:
        return "snr_20"
    if abs(snr - 10) < 0.01:
        return "snr_10"
    if abs(snr - 5) < 0.01:
        return "snr_5"
    if abs(snr) < 0.01:
        return "snr_0"
    return f"snr_{snr:g}"


def _rate(rows: list[dict[str, Any]], edits: str, denom: str, fallback: str) -> float | None:
    e = sum(int(_f(row.get(edits)) or 0) for row in rows if row.get("success"))
    d = sum(int(_f(row.get(denom)) or 0) for row in rows if row.get("success"))
    if d:
        return e / d
    values = [_f(row.get("metrics", {}).get(fallback)) for row in rows if row.get("success")]
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - index) + ordered[hi] * (index - lo)


def _group(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    return grouped


def _quality(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean = [row for row in rows if row["noise_key"] == "clean"]
    out = []
    for key, items in sorted(_group(clean, ("provider", "model", "dataset", "language", "acoustic_profile")).items()):
        success = [row for row in items if row["success"]]
        out.append({"provider": key[0], "model": key[1], "dataset": key[2], "language": key[3], "acoustic_profile": key[4], "samples": len({row.get("sample_id") for row in success}), "wer": _rate(success, "word_edits", "ref_words", "wer"), "cer": _rate(success, "char_edits", "ref_chars", "cer"), "ser": mean([0.0 if row.get("exact_match") else 1.0 for row in success]) if success else None, "exact_match_rate": mean([1.0 if row.get("exact_match") else 0.0 for row in success]) if success else None, "normalization_profile": "normalized-v1"})
    return out


def _performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model", "dataset", "language", "acoustic_profile")).items()):
        success = [row for row in items if row["success"]]
        lat = [_f(row.get("metrics", {}).get("end_to_end_latency_ms")) for row in success]
        rtf = [_f(row.get("metrics", {}).get("end_to_end_rtf")) for row in success]
        compute = [_f(row.get("metrics", {}).get("provider_compute_rtf")) for row in success]
        durations = sum(_f(row.get("audio_duration_sec")) or 0 for row in success)
        elapsed = sum((_f(row.get("metrics", {}).get("end_to_end_latency_ms")) or 0) / 1000 for row in success)
        mean_rtf = mean([v for v in rtf if v is not None]) if any(v is not None for v in rtf) else None
        flags = []
        if mean_rtf is not None and mean_rtf > 1:
            flags.append("embedded_rtf_gt_1")
        out.append({"provider": key[0], "model": key[1], "dataset": key[2], "language": key[3], "acoustic_profile": key[4], "samples": len(success), "final_latency_ms_p50": median([v for v in lat if v is not None]) if any(v is not None for v in lat) else None, "final_latency_ms_p95": _percentile([v for v in lat if v is not None], 0.95), "end_to_end_rtf_mean": mean_rtf, "end_to_end_rtf_p95": _percentile([v for v in rtf if v is not None], 0.95), "provider_compute_rtf_mean": mean([v for v in compute if v is not None]) if any(v is not None for v in compute) else None, "throughput_audio_sec_per_sec": durations / elapsed if elapsed else None, "admissible": not flags, "admissibility_flags": ";".join(flags)})
    return out


def _noise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model", "dataset", "language", "acoustic_profile")).items()):
        by_noise = {noise: [row for row in items if row["noise_key"] == noise] for noise in ("clean", "snr_20", "snr_10", "snr_5", "snr_0")}
        wers = {noise: _rate(sub, "word_edits", "ref_words", "wer") for noise, sub in by_noise.items()}
        noisy = [value for name, value in wers.items() if name != "clean" and value is not None]
        deg = (max(noisy) - wers["clean"]) * 100 if noisy and wers["clean"] is not None else None
        out.append({"provider": key[0], "model": key[1], "dataset": key[2], "language": key[3], "acoustic_profile": key[4], "clean_wer": wers["clean"], "snr_20_wer": wers["snr_20"], "snr_10_wer": wers["snr_10"], "snr_5_wer": wers["snr_5"], "snr_0_wer": wers["snr_0"], "noise_deg_pp": deg})
    for dataset in sorted({row["dataset"] for row in out}):
        ranked = sorted([row for row in out if row["dataset"] == dataset and row.get("noise_deg_pp") is not None], key=lambda row: row["noise_deg_pp"])
        for index, row in enumerate(ranked, start=1):
            row["robustness_rank_within_dataset"] = index
    return out


def _resource(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model", "dataset")).items()):
        success = [row for row in items if row["success"]]
        def values(metric: str) -> list[float]:
            return [v for v in (_f(row.get("metrics", {}).get(metric)) for row in success) if v is not None]
        meta = PROVIDER_META.get(key[0], {})
        available = any(values(metric) for metric in ("cpu_percent_mean", "memory_mb_peak", "gpu_util_percent_mean", "gpu_memory_mb_peak"))
        out.append({"provider": key[0], "model": key[1], "dataset": key[2], "device": meta.get("local_or_cloud", ""), "cpu_pct_mean": mean(values("cpu_percent_mean")) if values("cpu_percent_mean") else None, "cpu_pct_peak": max(values("cpu_percent_peak"), default=None), "ram_mb_peak": max(values("memory_mb_peak"), default=None), "gpu_util_pct_mean": mean(values("gpu_util_percent_mean")) if values("gpu_util_percent_mean") else None, "gpu_mem_mb_peak": max(values("gpu_memory_mb_peak"), default=None), "model_size_mb": None, "resource_metrics_available": available, "note_for_cloud_client_side_only": "cloud rows show client-side benchmark process resources only" if meta.get("local_or_cloud") == "cloud" else ""})
    return out


def _reliability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model", "dataset", "language", "acoustic_profile")).items()):
        total = len(items)
        success = sum(1 for row in items if row["success"])
        errors = [str(row.get("error_code") or row.get("error_message") or "") for row in items if not row["success"]]
        joined = " ".join(errors).lower()
        out.append({"provider": key[0], "model": key[1], "dataset": key[2], "language": key[3], "acoustic_profile": key[4], "total_attempts": total, "successful_attempts": success, "failed_attempts": total - success, "success_rate": success / total if total else None, "timeout_count": joined.count("timeout"), "rate_limit_count": joined.count("rate") + joined.count("quota"), "auth_error_count": joined.count("auth") + joined.count("credential"), "provider_error_count": sum(1 for err in errors if err), "oom_count": joined.count("out of memory") + joined.count("oom"), "sanitized_error_summary": "; ".join(sorted(set(errors)))[:400]})
    return out


def _cost(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model")).items()):
        success = [row for row in items if row["success"]]
        datasets = {row["dataset"] for row in success}
        duration = sum(_f(row.get("audio_duration_sec")) or 0 for row in success)
        costs = [_f(row.get("metrics", {}).get("estimated_cost_usd")) for row in success]
        estimated = sum(v for v in costs if v is not None)
        meta = PROVIDER_META.get(key[0], {})
        if meta.get("local_or_cloud") == "local":
            cost_type = "local_hardware_not_monetized"
            cost_hour: Any = 0.0
            estimated = 0.0
        elif estimated > 0 and duration > 0:
            cost_type = "cloud_estimated"
            cost_hour = estimated / (duration / 3600)
        else:
            cost_type = "cloud_not_estimated"
            cost_hour = "not_estimated"
        out.append({"provider": key[0], "model": key[1], "local_or_cloud": meta.get("local_or_cloud", ""), "dataset_count": len(datasets), "total_audio_duration_sec": duration, "estimated_cost_usd": estimated if cost_type != "cloud_not_estimated" else "not_estimated", "cost_per_audio_hour_usd": cost_hour, "cost_type": cost_type, "offline_capable": meta.get("offline_capable", ""), "internet_required": meta.get("internet_required", ""), "credentials_required": meta.get("credentials_required", ""), "ros2_suitability": meta.get("ros2_suitability", ""), "cocohrip_suitability": meta.get("cocohrip_suitability", "")})
    return out


def _dataset_matrix(q: list[dict[str, Any]], p: list[dict[str, Any]], r: list[dict[str, Any]]) -> list[dict[str, Any]]:
    perf = {(row["provider"], row["model"], row["dataset"]): row for row in p}
    rel = {(row["provider"], row["model"], row["dataset"]): row for row in r}
    out = []
    for row in q:
        key = (row["provider"], row["model"], row["dataset"])
        pr = perf.get(key, {})
        rr = rel.get(key, {})
        out.append({"provider": row["provider"], "model": row["model"], "dataset": row["dataset"], "language": row["language"], "acoustic_profile": row["acoustic_profile"], "wer": row["wer"], "rtf_mean": pr.get("end_to_end_rtf_mean"), "latency_p95": pr.get("final_latency_ms_p95"), "success_rate": rr.get("success_rate"), "benchmark_status": "success" if (rr.get("success_rate") or 0) > 0 else "failed"})
    return out


def _aggregate_matrix(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    out = []
    for key, items in sorted(_group(rows, ("provider", "model", field)).items()):
        out.append({"provider": key[0], "model": key[1], field: key[2], "datasets": ",".join(sorted({str(row["dataset"]) for row in items})), "total_samples": sum(int(row.get("samples") or 0) for row in items), "wer_mean": mean([row["wer"] for row in items if row.get("wer") is not None]) if any(row.get("wer") is not None for row in items) else None, "cer_mean": mean([row["cer"] for row in items if row.get("cer") is not None]) if any(row.get("cer") is not None for row in items) else None, "rtf_mean": None, "latency_p95": None, "success_rate": None})
    return out


def _domain_generalization(q: list[dict[str, Any]], p: list[dict[str, Any]]) -> list[dict[str, Any]]:
    perf = {(row["provider"], row["model"], row["dataset"]): row for row in p}
    baseline = {(row["provider"], row["model"]): row for row in q if row["dataset"] == "librispeech_test_clean_subset"}
    out = []
    for row in q:
        base = baseline.get((row["provider"], row["model"]), {})
        pr = perf.get((row["provider"], row["model"], row["dataset"]), {})
        bp = perf.get((row["provider"], row["model"], "librispeech_test_clean_subset"), {})
        wer_delta = row["wer"] - base["wer"] if row.get("wer") is not None and base.get("wer") is not None else None
        lat_delta = pr.get("final_latency_ms_p95") - bp.get("final_latency_ms_p95") if pr.get("final_latency_ms_p95") is not None and bp.get("final_latency_ms_p95") is not None else None
        rtf_delta = pr.get("end_to_end_rtf_mean") - bp.get("end_to_end_rtf_mean") if pr.get("end_to_end_rtf_mean") is not None and bp.get("end_to_end_rtf_mean") is not None else None
        out.append({"provider": row["provider"], "model": row["model"], "language": row["language"], "acoustic_profile": row["acoustic_profile"], "dataset": row["dataset"], "wer": row["wer"], "wer_delta_vs_clean_librispeech": wer_delta, "latency_delta_vs_clean_librispeech": lat_delta, "rtf_delta_vs_clean_librispeech": rtf_delta, "domain_robustness_note": "baseline clean LibriSpeech" if row["dataset"] == "librispeech_test_clean_subset" else "positive delta indicates degradation versus clean LibriSpeech"})
    return out


def _scenario_scores(q: list[dict[str, Any]], p: list[dict[str, Any]], c: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = defaultdict(list)
    for row in q:
        by_key[(row["provider"], row["model"])].append(row)
    perf_by_key = defaultdict(list)
    for row in p:
        perf_by_key[(row["provider"], row["model"])].append(row)
    cost = {(row["provider"], row["model"]): row for row in c}
    out = []
    for key, items in sorted(by_key.items()):
        wers = [row["wer"] for row in items if row.get("wer") is not None]
        rtfs = [row.get("end_to_end_rtf_mean") for row in perf_by_key.get(key, []) if row.get("end_to_end_rtf_mean") is not None]
        success_base = max(0.0, 100.0 * (1.0 - (mean(wers) if wers else 1.0)))
        rtf_bonus = 15.0 if rtfs and mean(rtfs) < 1 else 0.0
        local_bonus = 10.0 if cost.get(key, {}).get("local_or_cloud") == "local" else 0.0
        embedded = max(0.0, min(100.0, success_base + rtf_bonus + local_bonus))
        batch = max(0.0, min(100.0, success_base + 8.0))
        analytics = max(0.0, min(100.0, success_base + 5.0))
        dialog = max(0.0, min(100.0, success_base + rtf_bonus))
        scores = {"embedded": embedded, "batch": batch, "analytics": analytics, "dialog": dialog}
        best = max(scores, key=scores.get)
        out.append({"provider": key[0], "model": key[1], "dataset_scope": "extended_multi_dataset", "embedded_score": embedded, "batch_score": batch, "analytics_score": analytics, "dialog_score": dialog, "best_use_case": best, "final_recommendation": "heuristic decision-support score; inspect metric-family tables before selecting a provider"})
    return out


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _bar(path: Path, rows: list[dict[str, Any]], x: str, y: str, title: str, ylabel: str, threshold: float | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pairs = [(str(row.get(x, "")), _f(row.get(y))) for row in rows]
    pairs = [(label, value) for label, value in pairs if value is not None]
    fig, ax = plt.subplots(figsize=(11, 5))
    if pairs:
        ax.bar([p[0] for p in pairs], [p[1] for p in pairs], color="#0f766e")
    if threshold is not None:
        ax.axhline(threshold, linestyle="--", color="#b91c1c", linewidth=1.2)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _plots(output: Path, tables: dict[str, list[dict[str, Any]]]) -> None:
    plots = output / "plots"
    q_rows = [row for row in tables["quality_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    p_rows = [row for row in tables["performance_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    n_rows = [row for row in tables["noise_robustness_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    r_rows = [row for row in tables["reliability_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    lang_rows = [row for row in tables["provider_language_matrix.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    domain_rows = [row for row in tables["provider_domain_matrix.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    cost_rows = [row for row in tables["cost_deployment_table.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    matrix_rows = [row for row in tables["provider_dataset_matrix.csv"] if row.get("provider") not in PLOT_EXCLUDED_PROVIDERS]
    q = [{**row, "provider_dataset": f"{row['provider']}:{row['dataset']}"} for row in q_rows]
    p = [{**row, "provider_dataset": f"{row['provider']}:{row['dataset']}"} for row in p_rows]
    n = [{**row, "provider_dataset": f"{row['provider']}:{row['dataset']}"} for row in n_rows]
    r = [{**row, "provider_dataset": f"{row['provider']}:{row['dataset']}"} for row in r_rows]
    _bar(plots / "wer_by_provider_dataset.png", q, "provider_dataset", "wer", "WER by Provider and Dataset (lower is better)", "WER")
    _bar(plots / "wer_by_language_provider.png", lang_rows, "language", "wer_mean", "WER by Language and Provider (lower is better)", "WER")
    _bar(plots / "wer_by_domain_provider.png", domain_rows, "acoustic_profile", "wer_mean", "WER by Domain and Provider (lower is better)", "WER")
    _bar(plots / "latency_p95_by_provider_dataset.png", p, "provider_dataset", "final_latency_ms_p95", "P95 Latency by Provider and Dataset (lower is better)", "ms")
    _bar(plots / "rtf_by_provider_dataset.png", p, "provider_dataset", "end_to_end_rtf_mean", "End-to-End RTF by Provider and Dataset (RTF < 1 is faster than real time)", "RTF", threshold=1.0)
    _bar(plots / "noise_robustness_by_dataset_provider.png", n, "provider_dataset", "noise_deg_pp", "WER Degradation Under Synthetic Noise (lower is better)", "percentage points")
    _bar(plots / "domain_generalization_heatmap_wer.png", q, "dataset", "wer", "Domain Generalization WER Heatmap Input (lower is better)", "WER")
    _bar(plots / "language_generalization_heatmap_wer.png", lang_rows, "language", "wer_mean", "Language Generalization WER Heatmap Input (lower is better)", "WER")
    _bar(plots / "reliability_by_provider_dataset.png", r, "provider_dataset", "success_rate", "Reliability by Provider and Dataset (higher is better)", "success rate")
    _bar(plots / "cost_vs_quality_extended.png", cost_rows, "provider", "estimated_cost_usd", "Cost vs Quality Context (cost lower is better; inspect WER table)", "estimated USD")
    _bar(plots / "wer_vs_latency_pareto_extended.png", matrix_rows, "provider", "wer", "WER vs Latency Pareto Source (lower-left is better in table)", "WER")


def _report(output: Path, tables: dict[str, list[dict[str, Any]]], artifacts: list[str], registry: dict[str, dict[str, Any]]) -> None:
    datasets = [registry[key] for key in sorted(registry)]
    providers = sorted({row["provider"] for row in tables["provider_dataset_matrix.csv"]})
    lines = ["# Extended Multi-Dataset ASR Benchmark Report", "", "## Goal", "", "This report extends the baseline bachelor thesis evidence with a multi-dataset ASR benchmark across dataset families, languages and acoustic conditions.", "", "## Baseline Versus Extended Evidence", "", "The baseline evidence remains in `results/thesis_final/` and uses only `librispeech_test_clean_subset`. The extended evidence in `results/thesis_extended/` evaluates additional validated dataset subsets and must be interpreted as a separate extension layer.", "", "## Plot Scope", "", "Final extended plots exclude Hugging Face providers by thesis presentation choice. Hugging Face rows remain in CSV tables and raw artifacts for traceability, but they are not used as plotted series in `results/thesis_extended/plots/`.", "", "## Datasets", "", "| dataset_id | language | acoustic_profile | sample_count | source |", "|---|---|---|---:|---|"]
    for item in datasets:
        meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        lines.append(f"| {item['dataset_id']} | {meta.get('language', '')} | {meta.get('acoustic_profile', '')} | {item.get('sample_count', '')} | {meta.get('source_ref', '')} |")
    lines.extend(["", "## Providers", "", "| provider | local/cloud | credential status | benchmark status |", "|---|---|---|---|"])
    for provider in providers:
        meta = PROVIDER_META.get(provider, {})
        status = "success" if any(row["provider"] == provider and row.get("benchmark_status") == "success" for row in tables["provider_dataset_matrix.csv"]) else "failed_or_unavailable"
        credential = "not required" if meta.get("local_or_cloud") == "local" else "required if cloud run present"
        lines.append(f"| {provider} | {meta.get('local_or_cloud', '')} | {credential} | {status} |")
    lines.extend(["", "## Metric Family Rationale", "", "The extended benchmark keeps metric families separate because no single provider is universally best across quality, latency, robustness, resources, deployment constraints, language coverage and reliability.", "", "## Findings By Metric Family", "", "Recognition quality is reported per provider, dataset, language and acoustic profile in `quality_table.csv`. Lower WER/CER/SER is better.", "", "Performance and RTF are reported in `performance_table.csv`. RTF below 1.0 means faster-than-real-time processing.", "", "Noise robustness is reported in `noise_robustness_table.csv` using synthetic white-noise SNR variants where available.", "", "Resource usage is reported in `resource_table.csv`; cloud resource rows describe client-side benchmark process observations only.", "", "Cost and deployment constraints are reported in `cost_deployment_table.csv`. Local providers have zero direct API cost, while hardware and maintenance are not monetized.", "", "Dataset/domain generalization is reported in `domain_generalization_table.csv`, `provider_language_matrix.csv` and `provider_domain_matrix.csv`.", "", "Reliability and error behavior are reported in `reliability_table.csv` with sanitized error summaries.", "", "## ROS2/COCOHRIP Recommendation", "", "Use local providers when offline reproducibility and controlled robot-lab execution are required. Use cloud providers only when connectivity, credentials, latency variability and direct API cost are acceptable. The extended benchmark should be read as scenario trade-offs, not as one universal winner.", "", "## Limitations", "", "- Each dataset subset is controlled thesis-scale evidence, not a large-scale ASR corpus.", "- Synthetic white noise does not cover all real laboratory acoustic conditions.", "- Cloud latency depends on network, region and provider configuration.", "- Cloud runs are cost-controlled and may use fewer acoustic conditions than local runs.", "- Language/model mismatch can dominate multilingual results.", "- Provider failures are retained in reliability tables rather than hidden.", "", "## Canonical Extended Artifacts", ""])
    lines.extend(f"- `{path}`" for path in artifacts)
    lines.extend(["", "## Final Conclusion", "", "The extended benchmark supports a hybrid thesis conclusion: local ASR providers are preferable for reproducible offline ROS2 experiments, while cloud ASR providers are useful as optional connected baselines when their operational constraints are acceptable."])
    (output / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/benchmark_runs")
    parser.add_argument("--output", default="results/thesis_extended")
    args = parser.parse_args()
    output = Path(args.output)
    registry = _load_registry()
    rows, artifacts = _rows(Path(args.input), registry)
    q = _quality(rows)
    p = _performance(rows)
    n = _noise(rows)
    res = _resource(rows)
    rel = _reliability(rows)
    cost = _cost(rows)
    dataset = _dataset_matrix(q, p, rel)
    lang = _aggregate_matrix(q, "language")
    domain = _aggregate_matrix(q, "acoustic_profile")
    tables = {
        "quality_table.csv": q,
        "performance_table.csv": p,
        "noise_robustness_table.csv": n,
        "resource_table.csv": res,
        "cost_deployment_table.csv": cost,
        "scenario_scores.csv": _scenario_scores(q, p, cost),
        "domain_generalization_table.csv": _domain_generalization(q, p),
        "reliability_table.csv": rel,
        "provider_dataset_matrix.csv": dataset,
        "provider_language_matrix.csv": lang,
        "provider_domain_matrix.csv": domain,
    }
    for name, table_rows in tables.items():
        _write_csv(output / name, table_rows, TABLE_FIELDS[name])
    _plots(output, tables)
    manifest = {"created_at": datetime.now(UTC).isoformat(), "input": args.input, "output": args.output, "canonical_artifacts": artifacts, "tables": {name: _repo(output / name) for name in tables}, "plots_dir": _repo(output / "plots"), "final_report": _repo(output / "final_report.md"), "git_commit": _git("rev-parse", "HEAD"), "python": platform.python_version()}
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    _report(output, tables, artifacts, registry)
    print(json.dumps({"output": args.output, "artifacts": len(artifacts), "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
