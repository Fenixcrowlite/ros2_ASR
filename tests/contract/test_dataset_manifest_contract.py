from __future__ import annotations

import pytest
from asr_datasets.manifest import load_manifest


def test_dataset_manifest_contract_requires_expected_fields(repo_root) -> None:
    manifest_path = repo_root / "tests" / "fixtures" / "manifests" / "valid_dataset.jsonl"
    samples = load_manifest(str(manifest_path))

    first = samples[0]
    assert first.sample_id
    assert first.audio_path
    assert first.transcript
    assert first.language


def test_dataset_manifest_contract_rejects_duplicate_ids(repo_root) -> None:
    manifest_path = repo_root / "tests" / "fixtures" / "manifests" / "duplicate_sample_ids.jsonl"
    with pytest.raises(ValueError, match="duplicate sample_id"):
        load_manifest(str(manifest_path))
