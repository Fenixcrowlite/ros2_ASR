from __future__ import annotations

from pathlib import Path

import pytest
from asr_config import resolve_profile, validate_benchmark_payload
from asr_datasets.manifest import load_manifest


def _external_dataset_profile_ids(repo_root: Path) -> list[str]:
    return sorted(
        path.stem
        for path in (repo_root / "configs" / "datasets").glob("*_subset.yaml")
        if path.stem != "sample_dataset"
    )


def _external_benchmark_profile_ids(repo_root: Path) -> list[str]:
    return sorted(
        path.stem for path in (repo_root / "configs" / "benchmark").glob("*_subset_whisper.yaml")
    )


@pytest.mark.parametrize(
    "profile_id",
    _external_dataset_profile_ids(Path(__file__).resolve().parents[2]),
)
def test_external_dataset_profiles_resolve_and_load(repo_root: Path, profile_id: str) -> None:
    resolved = resolve_profile(
        profile_type="datasets",
        profile_id=profile_id,
        configs_root=str(repo_root / "configs"),
    )
    manifest_path = str(resolved.data.get("manifest_path", ""))
    assert manifest_path

    samples = load_manifest(manifest_path)
    assert len(samples) >= 2
    assert all(Path(sample.audio_path).exists() for sample in samples)


@pytest.mark.parametrize(
    "profile_id",
    _external_benchmark_profile_ids(Path(__file__).resolve().parents[2]),
)
def test_external_benchmark_profiles_validate(repo_root: Path, profile_id: str) -> None:
    resolved = resolve_profile(
        profile_type="benchmark",
        profile_id=profile_id,
        configs_root=str(repo_root / "configs"),
    )
    errors = validate_benchmark_payload(resolved.data)
    assert errors == []

    dataset_profile = str(resolved.data.get("dataset_profile", "")).split("/", 1)[-1]
    assert dataset_profile in _external_dataset_profile_ids(repo_root)
