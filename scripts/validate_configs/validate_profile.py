#!/usr/bin/env python3
"""Validate and resolve a profile with snapshot output."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


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


def main() -> None:
    from asr_config import (
        resolve_profile,
        validate_benchmark_payload,
        validate_metric_payload,
        validate_runtime_payload,
    )

    parser = argparse.ArgumentParser(description="Validate profile")
    parser.add_argument(
        "--type",
        required=True,
        choices=["runtime", "benchmark", "providers", "datasets", "metrics", "deployment", "gui"],
    )
    parser.add_argument("--id", required=True)
    args = parser.parse_args()

    resolved = resolve_profile(profile_type=args.type, profile_id=args.id, configs_root="configs")
    errors: list[str] = []
    if args.type == "runtime":
        errors = validate_runtime_payload(resolved.data)
    if args.type == "benchmark":
        errors = validate_benchmark_payload(resolved.data)
    if args.type == "metrics":
        errors = validate_metric_payload(resolved.data)

    if errors:
        print("INVALID")
        for item in errors:
            print(f"- {item}")
        raise SystemExit(1)

    print("VALID")
    print(f"snapshot: {resolved.snapshot_path}")


if __name__ == "__main__":
    main()
