#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def load_providers(configs_root: Path, profile: str, seen: set[str] | None = None) -> list[str]:
    normalized = str(profile).removeprefix("benchmark/")
    visited = set(seen or set())
    if normalized in visited:
        raise SystemExit(f"Circular benchmark inheritance detected: {normalized}")
    visited.add(normalized)

    path = configs_root / "benchmark" / f"{normalized}.yaml"
    if not path.is_file():
        raise SystemExit(f"Benchmark profile not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise SystemExit(f"Benchmark profile root must be an object: {path}")

    inherited: list[str] = []
    parents = payload.get("inherits", []) or []
    if not isinstance(parents, list):
        raise SystemExit(f"Benchmark profile inherits must be a list: {path}")
    for parent in parents:
        inherited.extend(load_providers(configs_root, str(parent), visited))

    providers = payload.get("providers")
    selected = providers if providers is not None else inherited
    if not isinstance(selected, list):
        raise SystemExit(f"Benchmark profile providers must be a list: {path}")

    result: list[str] = []
    for provider in selected:
        text = str(provider).strip()
        if text and text not in result:
            result.append(text)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="default_benchmark")
    parser.add_argument("--configs-root", default="configs")
    args = parser.parse_args()

    providers = load_providers(Path(args.configs_root), str(args.profile))
    if not providers:
        raise SystemExit(f"Benchmark provider list is empty: {args.profile}")
    for provider in providers:
        print(provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
