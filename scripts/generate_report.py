#!/usr/bin/env python3
"""Generate Markdown summary report from benchmark JSON artifacts."""

from __future__ import annotations

import argparse
import os
from statistics import mean

from asr_metrics.io import load_benchmark_json


def main() -> None:
    """Parse args and write aggregated benchmark report markdown."""
    parser = argparse.ArgumentParser(description="Generate benchmark markdown report")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = load_benchmark_json(args.input)
    if not records:
        raise SystemExit("No benchmark records found")

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
    lines.append("| Backend | WER | CER | Latency (ms) | RTF | Error Rate | Cost Estimate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for backend in backends:
        subset = [r for r in records if r.backend == backend]
        wer = mean(r.wer for r in subset)
        cer = mean(r.cer for r in subset)
        lat = mean(r.latency_ms for r in subset)
        rtf = mean(r.rtf for r in subset)
        err = mean(1.0 if not r.success else 0.0 for r in subset)
        cost = sum(r.cost_estimate for r in subset)
        row = (
            f"| {backend} | {wer:.3f} | {cer:.3f} | {lat:.1f} | "
            f"{rtf:.3f} | {err:.3f} | {cost:.4f} |"
        )
        lines.append(row)

    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    for plot_name in [
        "wer_cer_by_backend.png",
        "latency_by_backend.png",
        "rtf_by_backend.png",
    ]:
        plot_path = os.path.join("results", "plots", plot_name)
        if os.path.exists(plot_path):
            lines.append(f"- ![]({plot_path})")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
