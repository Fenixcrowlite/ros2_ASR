from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from asr_benchmark_core.models import BenchmarkRunRequest
from asr_benchmark_core.orchestrator import BenchmarkOrchestrator
from asr_provider_base import register_provider

from tests.utils.fakes import FakeProviderAdapter


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_benchmark_orchestrator_persists_complete_run_artifacts(tmp_path: Path, sample_wav: str) -> None:
    class FakeBenchProvider(FakeProviderAdapter):
        provider_id = "fake_bench_component"

    register_provider("fake_bench_component", FakeBenchProvider)
    configs = tmp_path / "configs"
    artifacts = tmp_path / "artifacts"
    registry = tmp_path / "datasets" / "registry" / "datasets.json"
    imported_audio = tmp_path / "datasets" / "imported" / "bench.wav"
    manifest_path = tmp_path / "datasets" / "manifests" / "bench.jsonl"

    imported_audio.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registry.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_wav, imported_audio)

    manifest_path.write_text(
        json.dumps(
            {
                "sample_id": "sample_00001",
                "audio_path": str(imported_audio),
                "transcript": "hello world",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_bench.yaml",
        {
            "provider_id": "fake_bench_component",
            "settings": {},
        },
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {
            "dataset_id": "bench_dataset",
            "manifest_path": str(manifest_path),
        },
    )
    _write_yaml(configs / "metrics" / "quality.yaml", {"metrics": ["wer", "cer", "sample_accuracy"]})
    _write_yaml(configs / "metrics" / "timing.yaml", {"metrics": ["total_latency_ms", "success_rate"]})
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_bench"],
            "metric_profiles": ["metrics/quality", "metrics/timing"],
        },
    )

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    )
    summary = orchestrator.run(
        BenchmarkRunRequest(
            benchmark_profile="bench",
            dataset_profile="bench_dataset",
            providers=["providers/fake_bench"],
            run_id="bench_component_run",
        )
    )

    run_dir = artifacts / "benchmark_runs" / "bench_component_run"
    assert summary.total_samples == 1
    assert summary.successful_samples == 1
    assert (run_dir / "manifest" / "run_manifest.json").exists()
    assert (run_dir / "metrics" / "results.json").exists()
    assert (run_dir / "metrics" / "results.csv").exists()
    assert (run_dir / "reports" / "summary.json").exists()
    assert (run_dir / "reports" / "summary.md").exists()
    assert "sample_accuracy" in summary.mean_metrics
