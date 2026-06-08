#!/usr/bin/env python3
"""Validate a selected ASR provider before launching runtime processes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_workspace_sources(root: Path) -> None:
    src_root = root / "ros2_ws" / "src"
    sys.path.insert(0, str(root))
    for package_dir in sorted(src_root.iterdir()):
        if package_dir.is_dir():
            sys.path.insert(0, str(package_dir))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--configs-root", default="configs")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    add_workspace_sources(root)

    try:
        from asr_provider_base.manager import ProviderManager

        manager = ProviderManager(configs_root=str(root / args.configs_root))
        provider = manager.create_from_profile(args.profile)
        provider.teardown()
    except Exception as exc:
        print(f"ERROR: selected provider is not ready: {args.profile}", file=sys.stderr)
        print(f"DETAIL: {exc}", file=sys.stderr)
        print("Fix the reported setup issue or choose another provider.", file=sys.stderr)
        return 1

    print(f"PASS: selected provider is ready: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
