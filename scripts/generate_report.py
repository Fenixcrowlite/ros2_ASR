#!/usr/bin/env python3
"""Generate Markdown summary report from benchmark JSON artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean


def _bootstrap_imports() -> None:
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


_bootstrap_imports()

from asr_metrics.io import load_benchmark_json  # noqa: E402
from asr_metrics.quality import text_quality_support  # noqa: E402


def _looks_like_legacy_benchmark_records(payload: object) -> bool:
    return isinstance(payload, list) and all(
        isinstance(item, dict) and "backend" in item for item in payload
    )


def _looks_like_canonical_summary(payload: object) -> bool:
    return isinstance(payload, dict) and "provider_summaries" in payload and "run_id" in payload


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


def _corpus_wer(records) -> float:
    supports = [
        text_quality_support(record.transcript_ref, record.transcript_hyp) for record in records
    ]
    numerator = sum(item.word_edits for item in supports)
    denominator = sum(item.reference_word_count for item in supports)
    return float(numerator) / float(denominator) if denominator > 0 else 0.0


def _corpus_cer(records) -> float:
    supports = [
        text_quality_support(record.transcript_ref, record.transcript_hyp) for record in records
    ]
    numerator = sum(item.char_edits for item in supports)
    denominator = sum(item.reference_char_count for item in supports)
    return float(numerator) / float(denominator) if denominator > 0 else 0.0


def _build_legacy_report(raw_payload: list[dict[str, object]], input_path: Path) -> list[str]:
    records = load_benchmark_json(str(input_path))
    if not records:
        raise SystemExit(f"No benchmark records found in: {input_path}")

    backends = sorted(set(r.backend for r in records))
    scenarios = sorted(set(r.scenario for r in records))

    lines: list[str] = []
    lines.append("# ASR Benchmark Report")
    lines.append("")
    lines.append(f"Records: {len(records)}")
    lines.append(f"Backends: {', '.join(backends)}")
    lines.append(f"Scenarios: {', '.join(scenarios)}")
    lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append(
        "| Backend | Corpus WER | Corpus CER | Mean Latency (ms) | "
        "Mean RTF | Error Rate | Estimated Total Cost (USD) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for backend in backends:
        subset = [r for r in records if r.backend == backend]
        wer = _corpus_wer(subset)
        cer = _corpus_cer(subset)
        lat = mean(r.latency_ms for r in subset)
        rtf = mean(r.rtf for r in subset)
        err = mean(1.0 if not r.success else 0.0 for r in subset)
        cost = sum(r.cost_estimate for r in subset)
        row = (
            f"| {backend} | {wer:.3f} | {cer:.3f} | {lat:.1f} | "
            f"{rtf:.3f} | {err:.3f} | {cost:.4f} |"
        )
        lines.append(row)

    return lines


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
                    f"{float(latency.get('total_latency_ms', 0.0) or 0.0):.1f}",
                    f"{float(latency.get('real_time_factor', 0.0) or 0.0):.3f}",
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
                f"latency_ms={float(metrics.get('total_latency_ms', 0.0) or 0.0):.1f}, "
                f"rtf={float(metrics.get('real_time_factor', 0.0) or 0.0):.3f}"
            )

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

    if _looks_like_legacy_benchmark_records(raw_payload):
        lines = _build_legacy_report(raw_payload, input_path)
    elif _looks_like_canonical_summary(raw_payload):
        lines = _build_canonical_summary_report(raw_payload)
    else:
        raise SystemExit(
            "Unsupported benchmark JSON schema. Expected legacy flat record list "
            "or canonical benchmark summary object."
        )

    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    plots_root = input_path.parent / "plots"
    for plot_name in [
        "wer_cer_by_backend.png",
        "latency_by_backend.png",
        "rtf_by_backend.png",
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
