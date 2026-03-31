from __future__ import annotations

import json
from pathlib import Path

import pytest
from asr_gateway.result_views import compare_runs, list_benchmark_history, run_detail
from fastapi import HTTPException

from tests.utils.project import seed_benchmark_run


def _read_json(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _clean_name(value: str, what: str) -> str:
    del what
    return value


def test_list_benchmark_history_merges_disk_and_memory(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    seed_benchmark_run(tmp_path, "bench_a", wer=0.0, cer=0.0)

    rows = list_benchmark_history(
        artifacts_root=artifacts_root,
        read_json=_read_json,
        benchmark_jobs={
            "bench_in_memory": {
                "state": "running",
                "started_at": "2026-03-24T00:00:00+00:00",
                "providers": ["providers/whisper_local"],
            }
        },
        limit=10,
    )

    assert rows[0]["run_id"] == "bench_in_memory"
    assert any(row["run_id"] == "bench_a" for row in rows)
    disk_row = next(row for row in rows if row["run_id"] == "bench_a")
    assert "metric_statistics" in disk_row
    assert "metric_metadata" in disk_row
    assert "provider_summaries" in disk_row


def test_list_benchmark_history_prefers_completed_artifacts_over_stale_failed_job_state(
    tmp_path: Path,
) -> None:
    artifacts_root = tmp_path / "artifacts"
    seed_benchmark_run(tmp_path, "bench_reconciled", wer=0.0, cer=0.0)

    rows = list_benchmark_history(
        artifacts_root=artifacts_root,
        read_json=_read_json,
        benchmark_jobs={
            "bench_reconciled": {
                "state": "failed",
                "message": "Timed out waiting for benchmark result",
                "completed_at": "2026-03-30T13:52:56+00:00",
            }
        },
        limit=10,
    )

    row = next(item for item in rows if item["run_id"] == "bench_reconciled")
    assert row["state"] == "completed"
    assert row["message"] == "Recovered from stored artifacts after gateway timeout"


def test_list_benchmark_history_marks_partial_artifact_run_as_interrupted(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / "benchmark_runs" / "bench_partial"
    (run_dir / "manifest").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_outputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest" / "run_manifest.json").write_text(
        json.dumps({"run_id": "bench_partial", "created_at": "2026-03-30T13:00:00+00:00"}),
        encoding="utf-8",
    )
    (run_dir / "raw_outputs" / "sample.json").write_text('{"ok": true}\n', encoding="utf-8")

    rows = list_benchmark_history(
        artifacts_root=artifacts_root,
        read_json=_read_json,
        benchmark_jobs={},
        limit=10,
    )

    row = next(item for item in rows if item["run_id"] == "bench_partial")
    assert row["state"] == "interrupted"
    assert row["message"] == "Run started but no final summary was written"


def test_run_detail_tolerates_non_list_results_payload(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    run_dir = seed_benchmark_run(tmp_path, "bench_broken", wer=0.1, cer=0.05)
    (run_dir / "metrics" / "results.json").write_text('{"unexpected": true}', encoding="utf-8")

    payload = run_detail(
        "bench_broken",
        artifacts_root=artifacts_root,
        clean_name=_clean_name,
        read_json=_read_json,
        benchmark_jobs={},
    )

    assert payload["results_head"] == []
    assert payload["results_count"] == 0
    assert "provider_summaries" in payload["summary"]


def test_run_detail_prefers_completed_artifacts_over_failed_job_state(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    seed_benchmark_run(tmp_path, "bench_detail_recovered", wer=0.1, cer=0.05)

    payload = run_detail(
        "bench_detail_recovered",
        artifacts_root=artifacts_root,
        clean_name=_clean_name,
        read_json=_read_json,
        benchmark_jobs={
            "bench_detail_recovered": {
                "state": "failed",
                "message": "Timed out waiting for benchmark result",
            }
        },
    )

    assert payload["state"] == "completed"
    assert payload["message"] == "Recovered from stored artifacts after gateway timeout"


def test_run_detail_hydrates_quality_details_from_dataset_manifest(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / "benchmark_runs" / "bench_detail"
    for rel in ("manifest", "reports", "metrics"):
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    dataset_manifest = tmp_path / "datasets" / "manifests" / "detail_dataset.jsonl"
    dataset_manifest.parent.mkdir(parents=True, exist_ok=True)
    dataset_manifest.write_text(
        json.dumps(
            {
                "sample_id": "sample_detail",
                "audio_path": "data/sample/detail.wav",
                "transcript": "Hello, world!",
                "language": "en-US",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    (run_dir / "manifest" / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": "bench_detail",
                "dataset_manifest": "datasets/manifests/detail_dataset.jsonl",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    (run_dir / "reports" / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics" / "results.json").write_text(
        json.dumps(
            [
                {
                    "sample_id": "sample_detail",
                    "text": "Hello world",
                    "metrics": {"wer": 0.0, "cer": 0.0},
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    payload = run_detail(
        "bench_detail",
        artifacts_root=artifacts_root,
        clean_name=_clean_name,
        read_json=_read_json,
        benchmark_jobs={},
    )

    row = payload["results_head"][0]
    assert row["reference_text"] == "Hello, world!"
    assert row["normalized_reference_text"] == "hello world"
    assert row["normalized_hypothesis_text"] == "hello world"
    assert row["quality_support"]["word_edits"] == 0
    assert row["quality_support"]["reference_word_count"] == 2


def test_run_detail_resolves_dataset_manifest_from_dataset_profile(tmp_path: Path) -> None:
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / "benchmark_runs" / "bench_profile_detail"
    for rel in ("manifest", "reports", "metrics"):
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    dataset_manifest = tmp_path / "datasets" / "manifests" / "profile_dataset.jsonl"
    dataset_manifest.parent.mkdir(parents=True, exist_ok=True)
    dataset_manifest.write_text(
        json.dumps(
            {
                "sample_id": "sample_profile",
                "audio_path": "data/sample/profile.wav",
                "transcript": "Numbers 123",
                "language": "en-US",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    dataset_profile = tmp_path / "configs" / "datasets" / "profile_dataset.yaml"
    dataset_profile.parent.mkdir(parents=True, exist_ok=True)
    dataset_profile.write_text(
        "dataset_id: profile_dataset\nmanifest_path: datasets/manifests/profile_dataset.jsonl\n",
        encoding="utf-8",
    )

    (run_dir / "manifest" / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": "bench_profile_detail",
                "dataset_profile": "datasets/profile_dataset",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    (run_dir / "reports" / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "metrics" / "results.json").write_text(
        json.dumps(
            [
                {
                    "sample_id": "sample_profile",
                    "text": "numbers 123",
                    "metrics": {"wer": 0.0, "cer": 0.0},
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    payload = run_detail(
        "bench_profile_detail",
        artifacts_root=artifacts_root,
        clean_name=_clean_name,
        read_json=_read_json,
        benchmark_jobs={},
    )

    row = payload["results_head"][0]
    assert row["reference_text"] == "Numbers 123"
    assert row["normalized_reference_text"] == "numbers 123"
    assert row["quality_support"]["wer"] == 0.0


def test_list_benchmark_history_preserves_sample_accuracy_independent_of_wer_cer(
    tmp_path: Path,
) -> None:
    artifacts_root = tmp_path / "artifacts"
    seed_benchmark_run(
        tmp_path,
        "bench_exact_match_rate",
        wer=0.0,
        cer=0.0,
        sample_accuracy=0.0,
    )

    rows = list_benchmark_history(
        artifacts_root=artifacts_root,
        read_json=_read_json,
        benchmark_jobs={},
        limit=10,
    )

    row = next(item for item in rows if item["run_id"] == "bench_exact_match_rate")
    assert row["quality_metrics"]["wer"] == 0.0
    assert row["quality_metrics"]["cer"] == 0.0
    assert row["quality_metrics"]["sample_accuracy"] == 0.0


def test_compare_runs_rejects_empty_run_ids() -> None:
    with pytest.raises(HTTPException) as exc:
        compare_runs([], [], detail_loader=lambda _run_id: {})
    assert exc.value.status_code == 400


def test_compare_runs_flattens_provider_summaries() -> None:
    payload = compare_runs(
        ["run_a", "run_b"],
        [],
        detail_loader=lambda run_id: {
            "run_id": run_id,
            "summary": {
                "provider_summaries": [
                    {
                        "provider_key": f"providers/{run_id}_alpha",
                        "provider_profile": f"providers/{run_id}_alpha",
                        "provider_preset": "balanced",
                        "mean_metrics": {"wer": 0.1 if run_id == "run_a" else 0.2},
                    },
                    {
                        "provider_key": f"providers/{run_id}_beta",
                        "provider_profile": f"providers/{run_id}_beta",
                        "provider_preset": "accurate",
                        "mean_metrics": {"wer": 0.05 if run_id == "run_a" else 0.15},
                    },
                ]
            },
        },
    )

    assert len(payload["subjects"]) == 4
    assert payload["table"][0]["metric"] == "wer"
    assert payload["table"][0]["best_run"].startswith("run_a::providers/run_a_beta")
