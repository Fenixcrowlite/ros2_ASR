#!/usr/bin/env python3
"""Export benchmark summary from run JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def _bootstrap_imports() -> None:
    current = Path(__file__).resolve()
    project_root = current.parents[2]
    src_root = project_root / "ros2_ws" / "src"

    paths = [project_root]
    if src_root.is_dir():
        paths.extend(path for path in src_root.iterdir() if path.is_dir())

    for candidate in reversed(paths):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)


_bootstrap_imports()

from asr_reporting import export_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Export markdown summary")
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    summary_path = Path(args.summary_json)
    if not summary_path.exists():
        raise SystemExit(f"Summary JSON not found: {summary_path}")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Summary JSON is invalid: {exc}") from exc
    if not isinstance(summary, dict):
        raise SystemExit(f"Summary JSON root must be an object: {summary_path}")

    bullets = [f"{k}: {v}" for k, v in summary.items()]
    path = export_markdown(args.output_md, f"Benchmark {summary.get('run_id', 'unknown')}", bullets)
    print(path)


if __name__ == "__main__":
    main()
