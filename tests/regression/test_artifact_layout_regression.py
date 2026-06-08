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


def test_benchmark_artifact_layout_regression(tmp_path: Path, sample_wav: str) -> None:
    class FakeRegressionProvider(FakeProviderAdapter):
        provider_id = "fake_regression_provider"

    register_provider("fake_regression_provider", FakeRegressionProvider)
    configs = tmp_path / "configs"
    artifacts = tmp_path / "artifacts"
    registry = tmp_path / "datasets" / "registry" / "datasets.json"
    audio = tmp_path / "datasets" / "imported" / "sample.wav"
    manifest = tmp_path / "datasets" / "manifests" / "regression.jsonl"

    audio.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    registry.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_wav, audio)
    manifest.write_text(
        json.dumps(
            {
                "sample_id": "sample_0001",
                "audio_path": str(audio),
                "transcript": "hello world",
                "language": "en-US",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(configs / "providers" / "fake_regression.yaml", {"provider_id": "fake_regression_provider", "settings": {}})
    _write_yaml(configs / "datasets" / "regression_dataset.yaml", {"dataset_id": "regression_dataset", "manifest_path": str(manifest)})
    _write_yaml(configs / "metrics" / "quality.yaml", {"metrics": ["wer", "cer", "sample_accuracy"]})
    _write_yaml(configs / "benchmark" / "regression.yaml", {"dataset_profile": "datasets/regression_dataset", "providers": ["providers/fake_regression"], "metric_profiles": ["metrics/quality"]})

    summary = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    ).run(
        BenchmarkRunRequest(
            benchmark_profile="regression",
            dataset_profile="regression_dataset",
            providers=["providers/fake_regression"],
            run_id="bench_regression_layout",
        )
    )

    run_dir = artifacts / "benchmark_runs" / "bench_regression_layout"
    expected_files = {
        "manifest/run_manifest.json",
        "metrics/results.json",
        "metrics/results.csv",
        "reports/summary.json",
        "reports/summary.md",
    }
    actual = {
        str(path.relative_to(run_dir))
        for path in run_dir.rglob("*")
        if path.is_file()
    }

    assert summary.run_id == "bench_regression_layout"
    assert expected_files <= actual
