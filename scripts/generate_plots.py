#!/usr/bin/env python3
"""Standalone plotting entry point.

Used when raw benchmark JSON already exists and only plots need regeneration.
"""

from __future__ import annotations

import argparse

from asr_metrics.io import load_benchmark_json
from asr_metrics.plotting import generate_all_plots


def main() -> None:
    """Parse CLI args, load JSON records, generate plot images."""
    parser = argparse.ArgumentParser(description="Generate ASR benchmark plots")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    records = load_benchmark_json(args.input_json)
    generate_all_plots(records, args.output_dir)


if __name__ == "__main__":
    main()
