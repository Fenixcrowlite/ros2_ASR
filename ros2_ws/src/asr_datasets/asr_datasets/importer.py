"""Dataset import helpers."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from asr_datasets.manifest import DatasetSample, load_manifest, save_manifest

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


def import_from_uploaded_files(
    *,
    files: list[dict[str, Any]],
    target_dataset_id: str,
    language: str = "en-US",
    imported_root: str = "datasets/imported",
    manifests_root: str = "datasets/manifests",
) -> tuple[str, int]:
    """Persist uploaded dataset files and build a manifest.

    Supported layouts:
    - `*.jsonl` manifest + referenced `*.wav` files
    - `*.wav` files with paired `*.txt` transcript files having the same stem
    """
    target_root = Path(imported_root) / target_dataset_id
    target_root.mkdir(parents=True, exist_ok=True)

    saved: dict[str, Path] = {}
    manifest_candidate: Path | None = None
    for item in files:
        name = str(item.get("name", "") or "").strip()
        payload = item.get("content", b"")
        if not name:
            continue
        relative_name = name.replace("\\", "/").split("/")[-1]
        if not relative_name:
            continue
        if relative_name in saved:
            raise ValueError(
                "Uploaded dataset bundle contains duplicate filenames after path normalization: "
                f"{relative_name}"
            )
        dest = target_root / relative_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        saved[relative_name] = dest
        if dest.suffix.lower() == ".jsonl":
            manifest_candidate = dest

    if manifest_candidate is not None:
        manifest_samples = load_manifest(str(manifest_candidate))
        missing_audio: list[str] = []
        for sample in manifest_samples:
            audio_name = Path(sample.audio_path).name
            if audio_name in saved:
                sample.audio_path = str(saved[audio_name])
            else:
                missing_audio.append(audio_name or sample.audio_path)
        if missing_audio:
            joined = ", ".join(missing_audio[:10])
            raise ValueError(
                "Uploaded manifest references audio files that were not included "
                "in the upload bundle: "
                f"{joined}"
            )
        manifest_out = Path(manifests_root) / f"{target_dataset_id}.jsonl"
        save_manifest(str(manifest_out), manifest_samples)
        return str(manifest_out), len(manifest_samples)

    wav_files = sorted(path for path in saved.values() if path.suffix.lower() in SUPPORTED_SUFFIXES)
    if not wav_files:
        raise ValueError("No WAV files found in uploaded selection")

    samples: list[DatasetSample] = []
    missing_transcripts: list[str] = []
    for index, audio in enumerate(wav_files):
        transcript_path = audio.with_suffix(".txt")
        transcript = (
            transcript_path.read_text(encoding="utf-8").strip() if transcript_path.exists() else ""
        )
        if not transcript:
            missing_transcripts.append(audio.name)
            continue
        samples.append(
            DatasetSample(
                sample_id=f"{target_dataset_id}_{index:05d}",
                audio_path=str(audio),
                transcript=transcript,
                language=language,
                split="test",
                tags=["uploaded"],
                metadata={"source": audio.name},
            )
        )

    if missing_transcripts:
        joined = ", ".join(missing_transcripts[:10])
        raise ValueError(
            "Uploaded samples require paired .txt transcripts with the same file "
            "stem when no manifest is provided: "
            f"{joined}"
        )

    manifest_path = Path(manifests_root) / f"{target_dataset_id}.jsonl"
    save_manifest(str(manifest_path), samples)
    return str(manifest_path), len(samples)
