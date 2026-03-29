"""Matplotlib plotting helpers for benchmark reports."""

from __future__ import annotations

import os
from collections import defaultdict
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from asr_metrics.models import BenchmarkRecord
from asr_metrics.quality import text_quality_support


def _aggregate_metric(records: list[BenchmarkRecord], metric: str) -> float:
    if metric == "wer":
        supports = [text_quality_support(rec.transcript_ref, rec.transcript_hyp) for rec in records]
        numerator = sum(item.word_edits for item in supports)
        denominator = sum(item.reference_word_count for item in supports)
        return float(numerator) / float(denominator) if denominator > 0 else 0.0
    if metric == "cer":
        supports = [text_quality_support(rec.transcript_ref, rec.transcript_hyp) for rec in records]
        numerator = sum(item.char_edits for item in supports)
        denominator = sum(item.reference_char_count for item in supports)
        return float(numerator) / float(denominator) if denominator > 0 else 0.0
    return float(mean(float(getattr(rec, metric)) for rec in records))


def _aggregate(records: list[BenchmarkRecord], metric: str) -> tuple[list[str], list[float]]:
    """Aggregate metric by backend using arithmetic mean."""
    grouped: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    for rec in records:
        grouped[rec.backend].append(rec)
    backends = sorted(grouped)
    values = [_aggregate_metric(grouped[b], metric) for b in backends]
    return backends, values


def _bar_plot(records: list[BenchmarkRecord], metric: str, ylabel: str, output_path: str) -> None:
    """Generate generic backend bar chart for one metric."""
    backends, values = _aggregate(records, metric)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(
        backends, values, color=["#0f766e", "#1d4ed8", "#b45309", "#475569", "#be123c", "#166534"]
    )
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Backend")
    ax.set_title(f"{ylabel} by Backend")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _scenario_latency(records: list[BenchmarkRecord], output_path: str) -> None:
    """Generate latency bar chart split by backend and scenario label."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for rec in records:
        key = f"{rec.backend}:{rec.scenario}"
        grouped[key].append(rec.latency_ms)
    labels = sorted(grouped)
    values = [mean(grouped[k]) for k in labels]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(labels, values, color="#0ea5e9")
    ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("Backend:Scenario")
    ax.set_title("Latency by Backend and Scenario")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _wer_cer_plot(records: list[BenchmarkRecord], output_path: str) -> None:
    """Generate combined WER/CER chart for backend comparison."""
    grouped_wer: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    grouped_cer: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    for rec in records:
        grouped_wer[rec.backend].append(rec)
        grouped_cer[rec.backend].append(rec)

    backends = sorted(grouped_wer)
    wer_values = [_aggregate_metric(grouped_wer[b], "wer") for b in backends]
    cer_values = [_aggregate_metric(grouped_cer[b], "cer") for b in backends]
    positions = list(range(len(backends)))

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([p - 0.2 for p in positions], wer_values, width=0.4, label="WER", color="#0f766e")
    ax.bar([p + 0.2 for p in positions], cer_values, width=0.4, label="CER", color="#b45309")
    ax.set_xticks(positions)
    ax.set_xticklabels(backends)
    ax.set_ylabel("Error Rate")
    ax.set_xlabel("Backend")
    ax.set_title("WER/CER by Backend")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def generate_all_plots(records: list[BenchmarkRecord], output_dir: str) -> None:
    """Generate full default plot set used by benchmark pipeline."""
    if not records:
        raise ValueError("No benchmark records provided for plotting")
    os.makedirs(output_dir, exist_ok=True)
    _wer_cer_plot(records, os.path.join(output_dir, "wer_cer_by_backend.png"))
    _bar_plot(records, "wer", "WER", os.path.join(output_dir, "wer_by_backend.png"))
    _bar_plot(
        records, "latency_ms", "Latency (ms)", os.path.join(output_dir, "latency_by_backend.png")
    )
    _bar_plot(records, "rtf", "RTF", os.path.join(output_dir, "rtf_by_backend.png"))
    _scenario_latency(records, os.path.join(output_dir, "latency_by_scenario.png"))
