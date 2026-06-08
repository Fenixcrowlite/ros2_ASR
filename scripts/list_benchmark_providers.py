#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="default_benchmark")
    parser.add_argument("--configs-root", default="configs")
    args = parser.parse_args()

    profile = str(args.profile).removeprefix("benchmark/")
    path = Path(args.configs_root) / "benchmark" / f"{profile}.yaml"
    if not path.is_file():
        raise SystemExit(f"Benchmark profile not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    providers = payload.get("providers", [])
    if not isinstance(providers, list):
        raise SystemExit(f"Benchmark profile providers must be a list: {path}")
    for provider in providers:
        text = str(provider).strip()
        if text:
            print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
