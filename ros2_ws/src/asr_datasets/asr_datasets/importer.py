"""Dataset import helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

from asr_datasets.manifest import DatasetSample, save_manifest


SUPPORTED_SUFFIXES = {".wav"}


def import_from_folder(
    *,
    source_folder: str,
    target_dataset_id: str,
    transcript_default: str = "",
    language: str = "en-US",
    imported_root: str = "datasets/imported",
    manifests_root: str = "datasets/manifests",
) -> tuple[str, int]:
    source = Path(source_folder)
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")

    target_root = Path(imported_root) / target_dataset_id
    target_root.mkdir(parents=True, exist_ok=True)

    samples: list[DatasetSample] = []
    for index, audio in enumerate(sorted(source.glob("**/*"))):
        if not audio.is_file() or audio.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        copied = target_root / audio.name
        shutil.copy2(audio, copied)
        samples.append(
            DatasetSample(
                sample_id=f"{target_dataset_id}_{index:05d}",
                audio_path=str(copied),
                transcript=transcript_default,
                language=language,
                split="test",
                tags=["imported"],
                metadata={"source": str(audio)},
            )
        )

    manifest_path = Path(manifests_root) / f"{target_dataset_id}.jsonl"
    save_manifest(str(manifest_path), samples)
    return str(manifest_path), len(samples)
