from __future__ import annotations

import json
from pathlib import Path

from asr_storage import ArtifactStore


def test_artifact_store_creates_runtime_and_benchmark_layouts(tmp_path: Path) -> None:
    store = ArtifactStore(root=str(tmp_path / "artifacts"))

    runtime_dir = store.make_runtime_session("session_001")
    benchmark_dir = store.make_benchmark_run("run_001")

    assert (runtime_dir / "raw").is_dir()
    assert (runtime_dir / "normalized").is_dir()
    assert (benchmark_dir / "manifest").is_dir()
    assert (benchmark_dir / "reports").is_dir()


def test_artifact_store_saves_outputs_and_metadata(tmp_path: Path) -> None:
    store = ArtifactStore(root=str(tmp_path / "artifacts"))
    run_dir = store.make_benchmark_run("run_002")

    manifest_ref = store.save_manifest(run_dir, {"run_id": "run_002"})
    metric_ref = store.save_metric(run_dir, "summary", {"wer": 0.1})
    report_ref = store.save_report(run_dir, "summary.md", "# Summary\n")

    assert manifest_ref.run_id == "run_002"
    assert metric_ref.artifact_type == "json"
    assert report_ref.artifact_type == "text"
    assert json.loads(Path(metric_ref.path).read_text(encoding="utf-8"))["wer"] == 0.1
    assert Path(report_ref.path).read_text(encoding="utf-8").startswith("# Summary")


def test_build_run_id_is_unique_even_within_same_second(tmp_path: Path) -> None:
    store = ArtifactStore(root=str(tmp_path / "artifacts"))

    first = store.build_run_id("bench")
    second = store.build_run_id("bench")

    assert first != second
    assert first.startswith("bench_")
    assert second.startswith("bench_")
