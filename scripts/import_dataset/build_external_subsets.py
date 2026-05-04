#!/usr/bin/env python3
"""Build reproducible small external dataset subsets for local benchmarks."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import tarfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import soundfile as sf
import yaml  # type: ignore[import-untyped]
from huggingface_hub import hf_hub_download

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_ROOT = PROJECT_ROOT / "configs"
DATASETS_ROOT = PROJECT_ROOT / "datasets"
IMPORT_ROOT = DATASETS_ROOT / "imported"
MANIFEST_ROOT = DATASETS_ROOT / "manifests"
REGISTRY_PATH = DATASETS_ROOT / "registry" / "datasets.json"
CACHE_DIR = PROJECT_ROOT / ".cache" / "external_datasets"


@dataclass(frozen=True, slots=True)
class ExternalSubsetSpec:
    dataset_id: str
    benchmark_id: str
    builder: str
    repo_id: str
    source_name: str
    source_ref: str
    source_url: str
    license_name: str
    language: str
    split: str
    acoustic_profile: str
    tags: tuple[str, ...]
    item_count: int = 2
    parquet_path: str = ""
    transcript_field: str = ""
    sample_id_field: str = ""
    hf_config: str = ""
    mls_audio_tar_path: str = ""
    mls_transcripts_path: str = ""
    mls_segments_path: str = ""


EXTERNAL_SUBSETS: tuple[ExternalSubsetSpec, ...] = (
    ExternalSubsetSpec(
        dataset_id="librispeech_test_clean_subset",
        benchmark_id="librispeech_test_clean_subset_whisper",
        builder="parquet",
        repo_id="openslr/librispeech_asr",
        parquet_path="all/test.clean/0000.parquet",
        transcript_field="text",
        sample_id_field="id",
        source_name="LibriSpeech",
        source_ref="OpenSLR SLR12 test-clean",
        source_url="https://www.openslr.org/12/",
        license_name="CC BY 4.0",
        language="en-US",
        split="test",
        acoustic_profile="clean_read",
        tags=("external", "librispeech", "clean", "read_speech", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="librispeech_test_other_subset",
        benchmark_id="librispeech_test_other_subset_whisper",
        builder="parquet",
        repo_id="openslr/librispeech_asr",
        parquet_path="all/test.other/0000.parquet",
        transcript_field="text",
        sample_id_field="id",
        source_name="LibriSpeech",
        source_ref="OpenSLR SLR12 test-other",
        source_url="https://www.openslr.org/12/",
        license_name="CC BY 4.0",
        language="en-US",
        split="test",
        acoustic_profile="harder_read",
        tags=("external", "librispeech", "other", "harder_condition", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="mini_librispeech_dev_clean_2_subset",
        benchmark_id="mini_librispeech_dev_clean_2_subset_whisper",
        builder="parquet",
        repo_id="openslr/librispeech_asr",
        parquet_path="all/validation.clean/0000.parquet",
        transcript_field="text",
        sample_id_field="id",
        source_name="Mini LibriSpeech",
        source_ref="OpenSLR SLR31 dev-clean-2",
        source_url="https://www.openslr.org/31/",
        license_name="CC BY 4.0",
        language="en-US",
        split="dev",
        acoustic_profile="clean_read",
        tags=("external", "mini_librispeech", "clean", "read_speech", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="fleurs_en_us_test_subset",
        benchmark_id="fleurs_en_us_test_subset_whisper",
        builder="fleurs",
        repo_id="google/fleurs",
        hf_config="en_us",
        source_name="FLEURS",
        source_ref="google/fleurs en_us test",
        source_url="https://huggingface.co/datasets/google/fleurs",
        license_name="CC BY 4.0",
        language="en-US",
        split="test",
        acoustic_profile="crowdsourced_mobile",
        tags=("external", "fleurs", "english", "crowdsourced", "mobile", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="fleurs_fr_fr_test_subset",
        benchmark_id="fleurs_fr_fr_test_subset_whisper",
        builder="fleurs",
        repo_id="google/fleurs",
        hf_config="fr_fr",
        source_name="FLEURS",
        source_ref="google/fleurs fr_fr test",
        source_url="https://huggingface.co/datasets/google/fleurs",
        license_name="CC BY 4.0",
        language="fr-FR",
        split="test",
        acoustic_profile="crowdsourced_mobile",
        tags=("external", "fleurs", "french", "crowdsourced", "mobile", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="fleurs_ja_jp_test_subset",
        benchmark_id="fleurs_ja_jp_test_subset_whisper",
        builder="fleurs",
        repo_id="google/fleurs",
        hf_config="ja_jp",
        source_name="FLEURS",
        source_ref="google/fleurs ja_jp test",
        source_url="https://huggingface.co/datasets/google/fleurs",
        license_name="CC BY 4.0",
        language="ja-JP",
        split="test",
        acoustic_profile="crowdsourced_mobile",
        tags=("external", "fleurs", "japanese", "crowdsourced", "mobile", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="fleurs_sk_sk_test_subset",
        benchmark_id="fleurs_sk_sk_test_subset_whisper",
        builder="fleurs",
        repo_id="google/fleurs",
        hf_config="sk_sk",
        source_name="FLEURS",
        source_ref="google/fleurs sk_sk test",
        source_url="https://huggingface.co/datasets/google/fleurs",
        license_name="CC BY 4.0",
        language="sk-SK",
        split="test",
        acoustic_profile="crowdsourced_mobile",
        tags=("external", "fleurs", "slovak", "crowdsourced", "mobile", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="voxpopuli_en_test_subset",
        benchmark_id="voxpopuli_en_test_subset_whisper",
        builder="parquet",
        repo_id="facebook/voxpopuli",
        parquet_path="en/test-00000-of-00001.parquet",
        transcript_field="normalized_text",
        sample_id_field="audio_id",
        source_name="VoxPopuli",
        source_ref="facebook/voxpopuli en test",
        source_url="https://huggingface.co/datasets/facebook/voxpopuli",
        license_name="CC BY-NC 4.0",
        language="en-US",
        split="test",
        acoustic_profile="far_field_plenary",
        tags=("external", "voxpopuli", "english", "parliament", "far_field", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="voxpopuli_de_test_subset",
        benchmark_id="voxpopuli_de_test_subset_whisper",
        builder="parquet",
        repo_id="facebook/voxpopuli",
        parquet_path="de/test-00000-of-00001.parquet",
        transcript_field="normalized_text",
        sample_id_field="audio_id",
        source_name="VoxPopuli",
        source_ref="facebook/voxpopuli de test",
        source_url="https://huggingface.co/datasets/facebook/voxpopuli",
        license_name="CC BY-NC 4.0",
        language="de-DE",
        split="test",
        acoustic_profile="far_field_plenary",
        tags=("external", "voxpopuli", "german", "parliament", "far_field", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="voxpopuli_es_test_subset",
        benchmark_id="voxpopuli_es_test_subset_whisper",
        builder="parquet",
        repo_id="facebook/voxpopuli",
        parquet_path="es/test-00000-of-00001.parquet",
        transcript_field="normalized_text",
        sample_id_field="audio_id",
        source_name="VoxPopuli",
        source_ref="facebook/voxpopuli es test",
        source_url="https://huggingface.co/datasets/facebook/voxpopuli",
        license_name="CC BY-NC 4.0",
        language="es-ES",
        split="test",
        acoustic_profile="far_field_plenary",
        tags=("external", "voxpopuli", "spanish", "parliament", "far_field", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="mls_german_test_subset",
        benchmark_id="mls_german_test_subset_whisper",
        builder="mls",
        repo_id="facebook/multilingual_librispeech",
        mls_audio_tar_path="data/mls_german/test/audio/1054_1599_000.tar.gz",
        mls_transcripts_path="data/mls_german/test/transcripts.txt",
        mls_segments_path="data/mls_german/test/segments.txt",
        source_name="Multilingual LibriSpeech",
        source_ref="facebook/multilingual_librispeech mls_german test",
        source_url="https://huggingface.co/datasets/facebook/multilingual_librispeech",
        license_name="CC BY 4.0",
        language="de-DE",
        split="test",
        acoustic_profile="multilingual_audiobook",
        tags=("external", "mls", "german", "audiobook", "read_speech", "subset"),
    ),
    ExternalSubsetSpec(
        dataset_id="mls_spanish_test_subset",
        benchmark_id="mls_spanish_test_subset_whisper",
        builder="mls",
        repo_id="facebook/multilingual_librispeech",
        mls_audio_tar_path="data/mls_spanish/test/audio/10667_6706_000.tar.gz",
        mls_transcripts_path="data/mls_spanish/test/transcripts.txt",
        mls_segments_path="data/mls_spanish/test/segments.txt",
        source_name="Multilingual LibriSpeech",
        source_ref="facebook/multilingual_librispeech mls_spanish test",
        source_url="https://huggingface.co/datasets/facebook/multilingual_librispeech",
        license_name="CC BY 4.0",
        language="es-ES",
        split="test",
        acoustic_profile="multilingual_audiobook",
        tags=("external", "mls", "spanish", "audiobook", "read_speech", "subset"),
    ),
)


def _safe_name(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._")
    return cleaned or "sample"


def _write_pcm16_wav_from_bytes(audio_bytes: bytes, target_path: Path) -> float:
    audio, sample_rate_hz = sf.read(io.BytesIO(audio_bytes))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(target_path), audio, sample_rate_hz, format="WAV", subtype="PCM_16")
    return float(len(audio) / float(sample_rate_hz))


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"datasets": []}
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("datasets registry root must be an object")
    datasets = payload.get("datasets", [])
    if not isinstance(datasets, list):
        raise ValueError("datasets registry must contain a list under `datasets`")
    payload["datasets"] = datasets
    return payload


def _save_registry(payload: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry_text = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    REGISTRY_PATH.write_text(registry_text, encoding="utf-8")


def _build_manifest_record(
    *,
    sample_id: str,
    dataset_id: str,
    transcript: str,
    language: str,
    duration_sec: float,
    split: str,
    tags: tuple[str, ...],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "audio_path": f"../imported/{dataset_id}/{_safe_name(sample_id)}.wav",
        "transcript": transcript,
        "language": language,
        "duration_sec": round(duration_sec, 3),
        "split": split,
        "tags": list(tags),
        "metadata": metadata,
    }


def _persist_subset(spec: ExternalSubsetSpec, records: list[dict[str, Any]]) -> None:
    if not records:
        raise ValueError(f"No samples were prepared for dataset `{spec.dataset_id}`")

    manifest_path = MANIFEST_ROOT / f"{spec.dataset_id}.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    dataset_profile = {
        "profile_id": f"datasets/{spec.dataset_id}",
        "inherits": [],
        "dataset_id": spec.dataset_id,
        "manifest_path": f"datasets/manifests/{spec.dataset_id}.jsonl",
        "default_language": spec.language,
    }
    benchmark_profile = {
        "profile_id": f"benchmark/{spec.benchmark_id}",
        "inherits": [],
        "dataset_profile": f"datasets/{spec.dataset_id}",
        "providers": ["providers/whisper_local"],
        "metric_profiles": ["metrics/default_quality", "metrics/default_timing"],
        "execution_mode": "batch",
        "batch": {"max_samples": 0, "timeout_sec": 240},
        "noise": {"mode": "white", "levels": ["clean"]},
    }

    dataset_profile_path = CONFIGS_ROOT / "datasets" / f"{spec.dataset_id}.yaml"
    benchmark_profile_path = CONFIGS_ROOT / "benchmark" / f"{spec.benchmark_id}.yaml"
    dataset_yaml = yaml.safe_dump(dataset_profile, sort_keys=False)
    benchmark_yaml = yaml.safe_dump(benchmark_profile, sort_keys=False)
    dataset_profile_path.write_text(dataset_yaml, encoding="utf-8")
    benchmark_profile_path.write_text(benchmark_yaml, encoding="utf-8")

    registry_payload = _load_registry()
    datasets = [
        item for item in registry_payload["datasets"] if item.get("dataset_id") != spec.dataset_id
    ]
    datasets.append(
        {
            "dataset_id": spec.dataset_id,
            "manifest_ref": str(manifest_path.relative_to(PROJECT_ROOT)),
            "sample_count": len(records),
            "metadata": {
                "source": "external_download",
                "source_ref": spec.source_ref,
                "source_url": spec.source_url,
                "language": spec.language,
                "acoustic_profile": spec.acoustic_profile,
                "license": spec.license_name,
            },
        }
    )
    registry_payload["datasets"] = sorted(
        datasets,
        key=lambda item: str(item.get("dataset_id", "")),
    )
    _save_registry(registry_payload)


def _build_parquet_subset(spec: ExternalSubsetSpec) -> list[dict[str, Any]]:
    parquet_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=spec.parquet_path,
        local_dir=str(CACHE_DIR),
    )
    parquet_file = pq.ParquetFile(parquet_path)
    records: list[dict[str, Any]] = []
    imported_root = IMPORT_ROOT / spec.dataset_id

    for batch in parquet_file.iter_batches(batch_size=32):
        for row in batch.to_pylist():
            transcript = str(row.get(spec.transcript_field, "") or "").strip()
            audio = row.get("audio") if isinstance(row.get("audio"), dict) else {}
            audio_bytes = audio.get("bytes") if isinstance(audio, dict) else None
            if not transcript or not audio_bytes:
                continue
            source_id = str(
                row.get(spec.sample_id_field, "") or Path(str(audio.get("path", ""))).stem
            )
            sample_id = _safe_name(source_id)
            target_path = imported_root / f"{sample_id}.wav"
            duration_sec = _write_pcm16_wav_from_bytes(audio_bytes, target_path)
            metadata = {
                "source": spec.source_name,
                "source_ref": spec.source_ref,
                "source_url": spec.source_url,
                "license": spec.license_name,
                "acoustic_profile": spec.acoustic_profile,
                "audio_format": "wav",
                "original_path": str(audio.get("path", "")),
                "original_format": Path(str(audio.get("path", ""))).suffix.lstrip(".").lower(),
            }
            for key in (
                "speaker_id",
                "chapter_id",
                "audio_id",
                "gender",
                "accent",
                "is_gold_transcript",
            ):
                value = row.get(key)
                if value not in ("", None):
                    metadata[key] = value
            records.append(
                _build_manifest_record(
                    sample_id=sample_id,
                    dataset_id=spec.dataset_id,
                    transcript=transcript,
                    language=spec.language,
                    duration_sec=duration_sec,
                    split=spec.split,
                    tags=spec.tags,
                    metadata=metadata,
                )
            )
            if len(records) >= spec.item_count:
                return records
    return records


def _build_fleurs_subset(spec: ExternalSubsetSpec) -> list[dict[str, Any]]:
    tsv_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=f"data/{spec.hf_config}/test.tsv",
        local_dir=str(CACHE_DIR),
    )
    tar_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=f"data/{spec.hf_config}/audio/test.tar.gz",
        local_dir=str(CACHE_DIR),
    )

    rows: list[list[str]] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 7:
                continue
            rows.append(row)

    records: list[dict[str, Any]] = []
    seen_transcripts: set[str] = set()
    imported_root = IMPORT_ROOT / spec.dataset_id
    with tarfile.open(tar_path, "r:gz") as archive:
        for phrase_id, filename, raw_text, normalized_text, _chars, frame_count, gender in rows:
            transcript = normalized_text.strip() or raw_text.strip()
            if not transcript or transcript in seen_transcripts:
                continue
            member = archive.extractfile(f"test/{filename}")
            if member is None:
                continue
            audio_bytes = member.read()
            sample_id = _safe_name(f"fleurs_{spec.hf_config}_{Path(filename).stem}")
            target_path = imported_root / f"{sample_id}.wav"
            duration_sec = _write_pcm16_wav_from_bytes(audio_bytes, target_path)
            metadata = {
                "source": spec.source_name,
                "source_ref": spec.source_ref,
                "source_url": spec.source_url,
                "license": spec.license_name,
                "acoustic_profile": spec.acoustic_profile,
                "fleurs_id": phrase_id,
                "gender": gender,
                "audio_format": "wav",
                "original_filename": filename,
                "raw_text": raw_text,
                "frame_count_24khz": int(frame_count),
            }
            records.append(
                _build_manifest_record(
                    sample_id=sample_id,
                    dataset_id=spec.dataset_id,
                    transcript=transcript,
                    language=spec.language,
                    duration_sec=duration_sec,
                    split=spec.split,
                    tags=spec.tags,
                    metadata=metadata,
                )
            )
            seen_transcripts.add(transcript)
            if len(records) >= spec.item_count:
                return records
    return records


def _load_tab_mapping(path: str) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            mapping[parts[0]] = parts[1:]
    return mapping


def _build_mls_subset(spec: ExternalSubsetSpec) -> list[dict[str, Any]]:
    audio_tar_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=spec.mls_audio_tar_path,
        local_dir=str(CACHE_DIR),
    )
    transcripts_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=spec.mls_transcripts_path,
        local_dir=str(CACHE_DIR),
    )
    segments_path = hf_hub_download(
        repo_id=spec.repo_id,
        repo_type="dataset",
        filename=spec.mls_segments_path,
        local_dir=str(CACHE_DIR),
    )
    transcripts = _load_tab_mapping(transcripts_path)
    segments = _load_tab_mapping(segments_path)

    records: list[dict[str, Any]] = []
    imported_root = IMPORT_ROOT / spec.dataset_id
    with tarfile.open(audio_tar_path, "r:gz") as archive:
        members = sorted(
            (
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.endswith(".flac")
            ),
            key=lambda member: member.name,
        )
        for member in members:
            sample_id = Path(member.name).stem
            transcript_parts = transcripts.get(sample_id, [])
            if not transcript_parts:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            duration_sec = _write_pcm16_wav_from_bytes(
                handle.read(),
                imported_root / f"{sample_id}.wav",
            )
            segment_parts = segments.get(sample_id, [])
            metadata: dict[str, Any] = {
                "source": spec.source_name,
                "source_ref": spec.source_ref,
                "source_url": spec.source_url,
                "license": spec.license_name,
                "acoustic_profile": spec.acoustic_profile,
                "audio_format": "wav",
                "original_format": "flac",
                "original_member": member.name,
            }
            if len(segment_parts) >= 3:
                metadata["source_audio_url"] = segment_parts[0]
                metadata["segment_start_sec"] = float(segment_parts[1])
                metadata["segment_end_sec"] = float(segment_parts[2])
            records.append(
                _build_manifest_record(
                    sample_id=sample_id,
                    dataset_id=spec.dataset_id,
                    transcript=transcript_parts[0].strip(),
                    language=spec.language,
                    duration_sec=duration_sec,
                    split=spec.split,
                    tags=spec.tags,
                    metadata=metadata,
                )
            )
            if len(records) >= spec.item_count:
                return records
    return records


def _build_subset(spec: ExternalSubsetSpec) -> list[dict[str, Any]]:
    if spec.builder == "parquet":
        return _build_parquet_subset(spec)
    if spec.builder == "fleurs":
        return _build_fleurs_subset(spec)
    if spec.builder == "mls":
        return _build_mls_subset(spec)
    raise ValueError(f"Unsupported builder: {spec.builder}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build reproducible external subset datasets")
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="Build only specific dataset_id values. Repeat to select multiple.",
    )
    parser.add_argument(
        "--item-count",
        type=int,
        default=0,
        help="Override the configured sample count for selected subsets.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = set(args.dataset_id)
    specs = [spec for spec in EXTERNAL_SUBSETS if not selected or spec.dataset_id in selected]
    if selected:
        unknown = sorted(selected - {spec.dataset_id for spec in EXTERNAL_SUBSETS})
        if unknown:
            raise SystemExit(f"Unknown dataset_id values: {', '.join(unknown)}")
    if args.item_count < 0:
        raise SystemExit("--item-count must be >= 0")
    if args.item_count:
        specs = [replace(spec, item_count=args.item_count) for spec in specs]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        records = _build_subset(spec)
        _persist_subset(spec, records)
        print(f"BUILT {spec.dataset_id}: {len(records)} samples")


if __name__ == "__main__":
    main()
