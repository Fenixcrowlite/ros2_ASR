#!/usr/bin/env python3
"""Generate Markdown summary report from benchmark JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _looks_like_canonical_summary(payload: object) -> bool:
    return isinstance(payload, dict) and "provider_summaries" in payload and "run_id" in payload


def _looks_like_schema_first_summary(payload: object) -> bool:
    return isinstance(payload, dict) and "manifest" in payload and "models" in payload


def _looks_like_final_manifest(payload: object) -> bool:
    return isinstance(payload, dict) and "tables" in payload and "final_report" in payload


def _first_metric(mapping: dict[str, object], *names: str) -> float:
    for name in names:
        value = mapping.get(name)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        return numeric
    return 0.0


def _format_provider_header(provider_summary: dict[str, object]) -> str:
    provider_profile = str(provider_summary.get("provider_profile", "") or "")
    provider_preset = str(provider_summary.get("provider_preset", "") or "")
    provider_id = str(provider_summary.get("provider_id", "") or "")
    if provider_profile and provider_preset:
        return f"{provider_profile} (preset={provider_preset})"
    if provider_profile:
        return provider_profile
    if provider_preset and provider_id:
        return f"{provider_id} (preset={provider_preset})"
    return provider_id or "unknown"


def _build_canonical_summary_report(summary_payload: dict[str, object]) -> list[str]:
    provider_summaries = summary_payload.get("provider_summaries", [])
    providers = provider_summaries if isinstance(provider_summaries, list) else []
    providers_value = summary_payload.get("providers", [])
    provider_labels = (
        [str(item) for item in providers_value]
        if isinstance(providers_value, list)
        else []
    )

    lines: list[str] = []
    lines.append("# ASR Benchmark Report")
    lines.append("")
    lines.append(f"Run ID: {summary_payload.get('run_id', '')}")
    lines.append(f"Benchmark Profile: {summary_payload.get('benchmark_profile', '')}")
    lines.append(f"Dataset ID: {summary_payload.get('dataset_id', '')}")
    lines.append(f"Execution Mode: {summary_payload.get('execution_mode', 'batch')}")
    lines.append(f"Aggregate Scope: {summary_payload.get('aggregate_scope', 'provider_only')}")
    lines.append(f"Providers: {', '.join(provider_labels)}")
    lines.append(f"Total Samples: {summary_payload.get('total_samples', 0)}")
    lines.append(f"Successful Samples: {summary_payload.get('successful_samples', 0)}")
    lines.append(f"Failed Samples: {summary_payload.get('failed_samples', 0)}")
    lines.append("")
    lines.append("## Provider Metrics")
    lines.append("")
    lines.append(
        "| Provider | WER | CER | Exact Match Rate | Mean Latency (ms) | "
        "Mean RTF | Success Rate | Estimated Total Cost (USD) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for item in providers:
        if not isinstance(item, dict):
            continue
        quality_metrics = item.get("quality_metrics", {})
        latency_metrics = item.get("latency_metrics", {})
        reliability_metrics = item.get("reliability_metrics", {})
        cost_totals = item.get("cost_totals", {})
        metric_statistics = item.get("metric_statistics", {})
        q = quality_metrics if isinstance(quality_metrics, dict) else {}
        latency = latency_metrics if isinstance(latency_metrics, dict) else {}
        r = reliability_metrics if isinstance(reliability_metrics, dict) else {}
        totals = cost_totals if isinstance(cost_totals, dict) else {}
        stats = metric_statistics if isinstance(metric_statistics, dict) else {}
        cost_stats = stats.get("estimated_cost_usd", {})
        c = cost_stats if isinstance(cost_stats, dict) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _format_provider_header(item),
                    f"{float(q.get('wer', 0.0) or 0.0):.3f}",
                    f"{float(q.get('cer', 0.0) or 0.0):.3f}",
                    f"{float(q.get('sample_accuracy', 0.0) or 0.0):.3f}",
                    f"{_first_metric(latency, 'end_to_end_latency_ms', 'provider_compute_latency_ms'):.1f}",
                    f"{_first_metric(latency, 'end_to_end_rtf', 'provider_compute_rtf'):.3f}",
                    f"{float(r.get('success_rate', 0.0) or 0.0):.3f}",
                    f"{float(totals.get('estimated_cost_usd', c.get('sum', 0.0)) or 0.0):.4f}",
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Noise Summary")
    lines.append("")
    noise_summary = summary_payload.get("noise_summary", {})
    noise_entries = noise_summary if isinstance(noise_summary, dict) else {}
    if not noise_entries:
        lines.append("- none")
    else:
        for noise_level, payload in sorted(noise_entries.items()):
            if not isinstance(payload, dict):
                continue
            mean_metrics = payload.get("mean_metrics", {})
            metrics = mean_metrics if isinstance(mean_metrics, dict) else {}
            lines.append(
                f"- {noise_level}: wer={float(metrics.get('wer', 0.0) or 0.0):.3f}, "
                f"cer={float(metrics.get('cer', 0.0) or 0.0):.3f}, "
                f"latency_ms={_first_metric(metrics, 'end_to_end_latency_ms', 'provider_compute_latency_ms'):.1f}, "
                f"rtf={_first_metric(metrics, 'end_to_end_rtf', 'provider_compute_rtf'):.3f}"
            )

    return lines


def _build_schema_first_report(summary_payload: dict[str, object]) -> list[str]:
    manifest_payload = summary_payload.get("manifest", {})
    manifest = manifest_payload if isinstance(manifest_payload, dict) else {}
    models_payload = summary_payload.get("models", [])
    models = models_payload if isinstance(models_payload, list) else []

    lines: list[str] = []
    lines.append("# ASR Benchmark Report")
    lines.append("")
    lines.append(f"Run ID: {manifest.get('run_id', '')}")
    lines.append(f"Scenario: {manifest.get('scenario', '')}")
    lines.append(f"Normalization Profile: {manifest.get('normalization_profile', '')}")
    lines.append("")
    lines.append("## Model Ranking")
    lines.append("")
    lines.append(
        "| Backend | Model | WER | CER | Final Latency p95 (ms) | "
        "RTF Mean | Scenario Score | Admissible | Flags |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---|---|")
    for item in models:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("backend", "")),
                    str(item.get("model", "")),
                    f"{float(item.get('wer', 0.0) or 0.0):.3f}",
                    f"{float(item.get('cer', 0.0) or 0.0):.3f}",
                    f"{float(item.get('final_latency_ms_p95', 0.0) or 0.0):.1f}",
                    f"{float(item.get('rtf_mean', 0.0) or 0.0):.3f}",
                    f"{float(item.get('scenario_score', 0.0) or 0.0):.1f}",
                    "yes" if bool(item.get("admissible", False)) else "no",
                    str(item.get("admissibility_flags", "")),
                ]
            )
            + " |"
        )
    return lines


def _build_final_manifest_report(manifest_payload: dict[str, object], input_path: Path) -> list[str]:
    tables_payload = manifest_payload.get("tables", {})
    tables = tables_payload if isinstance(tables_payload, dict) else {}
    output_root = input_path.parent
    existing_report = Path(str(manifest_payload.get("final_report", "") or ""))
    if existing_report and not existing_report.is_absolute():
        existing_report = output_root / existing_report.name
    if existing_report.exists():
        return existing_report.read_text(encoding="utf-8").splitlines()

    lines: list[str] = []
    lines.append("# Final ASR Benchmark Report")
    lines.append("")
    lines.append("## Artifact Manifest")
    lines.append("")
    lines.append(f"Created: {manifest_payload.get('created_at', '')}")
    lines.append(f"Run count: {manifest_payload.get('run_count', '')}")
    lines.append(f"Primary run count: {manifest_payload.get('primary_run_count', '')}")
    lines.append(f"Summary rows: {manifest_payload.get('summary_row_count', '')}")
    lines.append(f"Primary summary rows: {manifest_payload.get('primary_summary_row_count', '')}")
    lines.append(f"Primary utterance rows: {manifest_payload.get('primary_utterance_row_count', '')}")
    lines.append("")
    lines.append("## Tables")
    lines.append("")
    for table_name, table_path in sorted(tables.items()):
        path = Path(str(table_path))
        if not path.is_absolute():
            path = output_root / path.name
        row_count = 0
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                row_count = max(0, sum(1 for _ in handle) - 1)
        lines.append(f"- `{table_name}`: {row_count} rows")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Mock and fake providers are excluded from final benchmark tables.")
    lines.append("RTF means end-to-end real-time factor unless explicitly stated otherwise.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("The results are indicative unless the selected runs contain a sufficiently large sample set.")
    return lines


def main() -> None:
    """Parse args and write aggregated benchmark report markdown."""
    parser = argparse.ArgumentParser(description="Generate benchmark markdown report")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Benchmark JSON not found: {input_path}")
    try:
        raw_payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Benchmark JSON is invalid: {exc}") from exc

    if isinstance(raw_payload, list):
        raise SystemExit(
            "Flat benchmark result lists are no longer supported. Regenerate a canonical "
            "schema v2 benchmark summary and pass reports/summary.json."
        )
    elif _looks_like_canonical_summary(raw_payload):
        lines = _build_canonical_summary_report(raw_payload)
    elif _looks_like_schema_first_summary(raw_payload):
        lines = _build_schema_first_report(raw_payload)
    elif _looks_like_final_manifest(raw_payload):
        lines = _build_final_manifest_report(raw_payload, input_path)
    else:
        raise SystemExit(
            "Unsupported benchmark JSON schema. Expected canonical/schema-first/final "
            "benchmark summary object."
        )

    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    plots_root = input_path.parent / "plots"
    for plot_name in [
        "wer_cer_by_backend.png",
        "latency_by_backend.png",
        "rtf_by_backend.png",
        "pareto_wer_latency.png",
        "pareto_wer_energy.png",
        "latency_boxplot.png",
        "robustness_wer_by_snr.png",
        "accent_disparity.png",
        "calibration_reliability.png",
        "scenario_score.png",
    ]:
        plot_path = plots_root / plot_name
        if plot_path.exists():
            lines.append(f"- ![]({plot_path})")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
