#!/usr/bin/env python3
"""Export benchmark summary from run JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from asr_reporting import export_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Export markdown summary")
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    bullets = [f"{k}: {v}" for k, v in summary.items()]
    path = export_markdown(args.output_md, f"Benchmark {summary.get('run_id', 'unknown')}", bullets)
    print(path)


if __name__ == "__main__":
    main()
