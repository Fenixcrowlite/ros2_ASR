#!/usr/bin/env python3
"""Import WAV files from folder into normalized dataset manifest/registry."""

from __future__ import annotations

import argparse

from asr_datasets import DatasetEntry, DatasetRegistry, import_from_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Import folder as dataset")
    parser.add_argument("--source", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--transcript-default", default="")
    parser.add_argument("--registry", default="datasets/registry/datasets.json")
    args = parser.parse_args()

    manifest_path, count = import_from_folder(
        source_folder=args.source,
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
