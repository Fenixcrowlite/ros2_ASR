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


def test_compare_runs_rejects_empty_run_ids() -> None:
    with pytest.raises(HTTPException) as exc:
        compare_runs([], [], detail_loader=lambda _run_id: {})
    assert exc.value.status_code == 400
