#!/usr/bin/env python3
"""Generate Markdown summary report from benchmark JSON artifacts."""

from __future__ import annotations

import argparse
import json
import os
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

from asr_metrics.io import load_benchmark_json


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

    records = load_benchmark_json(str(input_path))
    if not records:
        raise SystemExit(f"No benchmark records found in: {input_path}")
    if not isinstance(raw_payload, list):
        raise SystemExit(f"Benchmark JSON root must be a list of records: {input_path}")

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

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
