#!/usr/bin/env python3
"""Import WAV files from folder into normalized dataset manifest/registry."""

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

from asr_datasets import DatasetEntry, DatasetRegistry, import_from_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Import folder as dataset")
    parser.add_argument("--source", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--transcript-default", default="")
    parser.add_argument("--registry", default="datasets/registry/datasets.json")
    args = parser.parse_args()
    source_path = Path(args.source)
    if not source_path.exists():
        raise SystemExit(f"Source folder not found: {source_path}")
    if not source_path.is_dir():
        raise SystemExit(f"Source path is not a directory: {source_path}")

    manifest_path, count = import_from_folder(
        source_folder=str(source_path),
        target_dataset_id=args.dataset_id,
        transcript_default=args.transcript_default,
        language=args.language,
    )
    registry = DatasetRegistry(args.registry)
    registry.register(
        DatasetEntry(
            dataset_id=args.dataset_id,
            manifest_ref=manifest_path,
            sample_count=count,
            metadata={"import_source": args.source},
        )
    )
    print(f"Imported dataset '{args.dataset_id}': {count} samples -> {manifest_path}")


if __name__ == "__main__":
    main()
