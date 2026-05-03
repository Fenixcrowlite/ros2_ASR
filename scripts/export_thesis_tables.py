#!/usr/bin/env python3
"""Export thesis-ready ASR comparison tables from schema-first run artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

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
    ],
    "quality_table.csv": [
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
        runs.append(
            {
                "run_dir": run_dir,
                "summary": payload,
                "manifest": manifest if isinstance(manifest, dict) else {},
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
            return thesis_runs
    return runs


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
        for row in run["models"]:
            backend = str(row.get("backend", "") or "")
            provider = _provider_from_backend(backend)
            if _is_mock_provider(provider, backend):
                continue
            rows.append(
                {
                    **row,
                    "provider": provider,
                    "normalization_profile": normalization_profile,
                    "run_id": str(row.get("run_id") or manifest.get("run_id") or ""),
                }
            )
    return rows


def _selected_utterance_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        for row in run["utterances"]:
            backend = str(row.get("backend", "") or "")
            provider = _provider_from_backend(backend)
            if _is_mock_provider(provider, backend):
                continue
            rows.append({**row, "provider": provider})
    return rows


def _provider_comparison_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tested = {str(row.get("provider", "") or "") for row in summary_rows}
    providers = [provider for provider in PROVIDER_CATALOG if provider in tested]
    providers.extend(provider for provider in PROVIDER_CATALOG if provider not in tested)
    return [{field: PROVIDER_CATALOG[provider].get(field, "") for field in TABLE_FIELDS["provider_comparison.csv"]} for provider in providers]


def _quality_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "provider": row.get("provider", ""),
            "model": row.get("model", ""),
            "dataset": row.get("dataset", ""),
            "language": row.get("language", ""),
            "samples": row.get("num_utterances", ""),
            "wer": row.get("wer", ""),
            "cer": row.get("cer", ""),
            "ser": row.get("ser", ""),
            "ci_95_low": row.get("ci_95_low", ""),
            "ci_95_high": row.get("ci_95_high", ""),
            "normalization_profile": row.get("normalization_profile", ""),
        }
        for row in summary_rows
    ]


def _performance_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
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
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in utterance_rows:
        by_key[(str(row.get("provider", "") or ""), str(row.get("model", "") or ""))].append(row)

    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for summary in summary_rows:
        key = (str(summary.get("provider", "") or ""), str(summary.get("model", "") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows = by_key.get(key, [])
        cpu_peaks = [_as_float(row.get("cpu_pct_peak")) for row in rows]
        gpu_utils = [_as_float(row.get("gpu_util_pct_mean")) for row in rows]
        output.append(
            {
                "provider": key[0],
                "model": key[1],
                "device": "cloud" if PROVIDER_CATALOG.get(key[0], {}).get("local_or_cloud") == "cloud" else "local",
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
    grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in utterance_rows:
        grouped[(str(row.get("provider", "") or ""), str(row.get("model", "") or ""))][_snr_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for (provider, model), by_snr in sorted(grouped.items()):
        clean_wer = _wer_for_rows(by_snr.get("clean", []))
        snr_wers = {key: _wer_for_rows(by_snr.get(key, [])) for key in ("snr_20", "snr_10", "snr_5", "snr_0")}
        noisy_values = [value for value in snr_wers.values() if value is not None]
        noise_deg_pp = None
        if clean_wer is not None and noisy_values:
            noise_deg_pp = (max(noisy_values) - clean_wer) * 100.0
        output.append(
            {
                "provider": provider,
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
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in summary_rows:
        provider = str(row.get("provider", "") or "")
        model = str(row.get("model", "") or "")
        key = (provider, model)
        if key in seen:
            continue
        seen.add(key)
        meta = PROVIDER_CATALOG.get(provider, {})
        output.append(
            {
                "provider": provider,
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
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in summary_rows:
        score = _as_float(row.get("scenario_score"))
        if score is None:
            continue
        grouped[(str(row.get("provider", "") or ""), str(row.get("model", "") or ""))][str(row.get("scenario", "") or "")] = score

    output: list[dict[str, Any]] = []
    for (provider, model), scores in sorted(grouped.items()):
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
    tables: dict[str, list[dict[str, Any]]],
) -> None:
    tested = sorted({str(row.get("provider", "") or "") for row in summary_rows})
    skipped = [provider for provider in PROVIDER_CATALOG if provider not in tested]
    min_samples = min((int(row.get("num_utterances") or 0) for row in summary_rows), default=0)
    calibration_valid = any(_as_bool(row.get("calibration_valid")) for row in summary_rows)
    has_cloud = any(PROVIDER_CATALOG.get(provider, {}).get("local_or_cloud") == "cloud" for provider in tested)

    lines = [
        "# Final Thesis ASR Benchmark Report",
        "",
        "## Goal And Thesis Alignment",
        "",
        "This report summarizes a bachelor thesis prototype for ROS2 ASR integration and experimental comparison of selected commercial and non-commercial ASR systems.",
        "",
        "## Tested Providers",
        "",
        f"Actually tested providers: {', '.join(tested) if tested else 'none'}",
        f"Skipped or not present in selected run artifacts: {', '.join(skipped) if skipped else 'none'}",
        "",
        "## Dataset Description",
        "",
        f"Selected schema-first runs: {len(runs)}",
        f"Minimum per-row sample count: {min_samples}",
        "Sample counts in these tables are utterance-variant rows and include clean/noisy SNR variants.",
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
        "Mock and fake providers are excluded from final thesis tables.",
        "",
        "## Metric Definitions",
        "",
        "WER/CER/SER measure recognition quality. Final latency and end-to-end RTF measure ROS2/operator-facing performance. `provider_compute_rtf` is secondary and `real_time_factor` is a deprecated compatibility alias.",
        "RTF in this thesis means end-to-end real-time factor unless explicitly stated otherwise.",
        "",
        "## Tables Summary",
        "",
    ]
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
    if min_samples and min_samples < 30:
        lines.append("The results are indicative and suitable for bachelor-thesis prototype evaluation, but not a large-scale ASR benchmark.")
    if not calibration_valid:
        lines.append("Confidence calibration is diagnostic only unless at least 30 confidence-bearing utterances are available.")
    if not has_cloud:
        lines.append("Cloud provider results are absent from the selected run artifacts; cloud comparison remains pending until credentials and runs are available.")
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
    primary_summary_rows = _selected_summary_rows(primary_runs)
    primary_utterance_rows = _selected_utterance_rows(primary_runs)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "provider_comparison.csv": _provider_comparison_rows(summary_rows),
        "quality_table.csv": _quality_rows(primary_summary_rows),
        "performance_table.csv": _performance_rows(primary_summary_rows),
        "resource_table.csv": _resource_rows(primary_summary_rows, primary_utterance_rows),
        "noise_robustness_table.csv": _noise_rows(primary_utterance_rows),
        "cost_deployment_table.csv": _cost_rows(primary_summary_rows),
        "scenario_scores.csv": _scenario_rows(summary_rows),
    }
    for table_name, rows in tables.items():
        _write_csv(output_dir / table_name, rows, TABLE_FIELDS[table_name])

    _generate_plots(output_dir, tables)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "input": str(Path(args.input)),
        "output": str(output_dir),
        "run_count": len(runs),
        "primary_run_count": len(primary_runs),
        "summary_row_count": len(summary_rows),
        "primary_summary_row_count": len(primary_summary_rows),
        "primary_utterance_row_count": len(primary_utterance_rows),
        "excluded_providers": "mock/fake providers",
        "tables": {name: str(output_dir / name) for name in tables},
        "plots_dir": str(output_dir / "plots"),
        "final_report": str(output_dir / "final_report.md"),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_final_report(
        output_dir / "final_report.md",
        runs=runs,
        summary_rows=summary_rows,
        tables=tables,
    )
    print(json.dumps({"output": str(output_dir), "run_count": len(runs)}, indent=2))


if __name__ == "__main__":
    main()
