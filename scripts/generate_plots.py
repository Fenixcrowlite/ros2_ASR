#!/usr/bin/env python3
"""Standalone plotting entry point.

Used when raw benchmark JSON already exists and only plots need regeneration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


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
from asr_metrics.plotting import generate_all_plots


def main() -> None:
    """Parse CLI args, load JSON records, generate plot images."""
    parser = argparse.ArgumentParser(description="Generate ASR benchmark plots")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    input_path = Path(args.input_json)
    if not input_path.exists():
        raise SystemExit(f"Benchmark JSON not found: {input_path}")

    records = load_benchmark_json(str(input_path))
    if not records:
        raise SystemExit(f"No benchmark records found in: {input_path}")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_all_plots(records, str(output_dir))


if __name__ == "__main__":
    main()
