from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from asr_benchmark_core.models import BenchmarkRunRequest
from asr_benchmark_core.orchestrator import BenchmarkOrchestrator
from asr_core.audio import wav_duration_sec
from asr_provider_base import register_provider

from tests.utils.fakes import FakeProviderAdapter


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_benchmark_orchestrator_persists_complete_run_artifacts(
    tmp_path: Path, sample_wav: str
) -> None:
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
    _write_yaml(
        configs / "metrics" / "quality.yaml", {"metrics": ["wer", "cer", "sample_accuracy"]}
    )
    _write_yaml(
        configs / "metrics" / "timing.yaml", {"metrics": ["total_latency_ms", "success_rate"]}
    )
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
    summary_payload = json.loads((run_dir / "reports" / "summary.json").read_text(encoding="utf-8"))
    assert len(summary_payload["provider_summaries"]) == 1
    assert summary_payload["provider_summaries"][0]["provider_profile"] == "providers/fake_bench"


def test_benchmark_orchestrator_persists_per_provider_summary_for_multi_provider_runs(
    tmp_path: Path, sample_wav: str
) -> None:
    class FakeBenchProviderA(FakeProviderAdapter):
        provider_id = "fake_provider_a"

    class FakeBenchProviderB(FakeProviderAdapter):
        provider_id = "fake_provider_b"

    register_provider("fake_provider_a", FakeBenchProviderA)
    register_provider("fake_provider_b", FakeBenchProviderB)
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
        configs / "providers" / "provider_a.yaml",
        {"provider_id": "fake_provider_a", "settings": {}},
    )
    _write_yaml(
        configs / "providers" / "provider_b.yaml",
        {"provider_id": "fake_provider_b", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(
        configs / "metrics" / "quality.yaml", {"metrics": ["wer", "cer", "sample_accuracy"]}
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/provider_a", "providers/provider_b"],
            "metric_profiles": ["metrics/quality"],
        },
    )

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    )
    orchestrator.run(
        BenchmarkRunRequest(
            benchmark_profile="bench",
            dataset_profile="bench_dataset",
            providers=["providers/provider_a", "providers/provider_b"],
            run_id="bench_multi_provider_run",
        )
    )

    run_dir = artifacts / "benchmark_runs" / "bench_multi_provider_run"
    summary_payload = json.loads((run_dir / "reports" / "summary.json").read_text(encoding="utf-8"))
    summary_markdown = (run_dir / "reports" / "summary.md").read_text(encoding="utf-8")

    assert summary_payload["aggregate_scope"] == "provider_only"
    assert summary_payload["mean_metrics"] == {}
    assert summary_payload["quality_metrics"] == {}
    assert len(summary_payload["provider_summaries"]) == 2
    assert {entry["provider_profile"] for entry in summary_payload["provider_summaries"]} == {
        "providers/provider_a",
        "providers/provider_b",
    }
    assert "## Per-Provider Summary" in summary_markdown
    assert "providers/provider_a" in summary_markdown
    assert "providers/provider_b" in summary_markdown


def test_benchmark_orchestrator_streaming_records_streaming_metrics(
    tmp_path: Path, sample_wav: str
) -> None:
    class FakeStreamingProvider(FakeProviderAdapter):
        provider_id = "fake_stream_component"

    register_provider("fake_stream_component", FakeStreamingProvider)
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
                "transcript": "stream 8 chunks",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_stream.yaml",
        {"provider_id": "fake_stream_component", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(
        configs / "metrics" / "streaming.yaml",
        {
            "metrics": [
                "wer",
                "first_partial_latency_ms",
                "finalization_latency_ms",
                "partial_count",
            ]
        },
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_stream"],
            "metric_profiles": ["metrics/streaming"],
            "execution_mode": "streaming",
            "streaming": {"chunk_ms": 250},
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
            providers=["providers/fake_stream"],
            benchmark_settings={"execution_mode": "streaming", "streaming": {"chunk_ms": 250}},
            run_id="bench_streaming_run",
        )
    )

    assert summary.metadata["execution_mode"] == "streaming"
    assert summary.mean_metrics["partial_count"] > 0
    assert summary.mean_metrics["first_partial_latency_ms"] > 0


def test_benchmark_orchestrator_streaming_replays_audio_in_real_time_by_default(
    tmp_path: Path,
    sample_wav: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asr_benchmark_core.executor as executor_module

    class FakeStreamingProvider(FakeProviderAdapter):
        provider_id = "fake_stream_paced_component"

    register_provider("fake_stream_paced_component", FakeStreamingProvider)
    sleep_calls: list[float] = []
    monkeypatch.setattr(executor_module, "sleep", lambda delay: sleep_calls.append(delay))

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
                "transcript": "stream 8 chunks",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_stream.yaml",
        {"provider_id": "fake_stream_paced_component", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(configs / "metrics" / "streaming.yaml", {"metrics": ["wer"]})
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_stream"],
            "metric_profiles": ["metrics/streaming"],
            "execution_mode": "streaming",
            "streaming": {"chunk_ms": 250, "replay_rate": 1.0},
        },
    )

    BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    ).run(
        BenchmarkRunRequest(
            benchmark_profile="bench",
            dataset_profile="bench_dataset",
            providers=["providers/fake_stream"],
            run_id="bench_streaming_paced",
        )
    )

    assert sleep_calls
    assert any(delay > 0 for delay in sleep_calls)


def test_benchmark_orchestrator_rejects_streaming_for_non_streaming_provider(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeBatchOnlyProvider(FakeProviderAdapter):
        provider_id = "fake_batch_only_component"

        def __init__(self) -> None:
            super().__init__(supports_streaming=False)

    register_provider("fake_batch_only_component", FakeBatchOnlyProvider)
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
        configs / "providers" / "fake_batch_only.yaml",
        {"provider_id": "fake_batch_only_component", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(configs / "metrics" / "streaming.yaml", {"metrics": ["wer"]})
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_batch_only"],
            "metric_profiles": ["metrics/streaming"],
            "execution_mode": "streaming",
            "streaming": {"chunk_ms": 250},
        },
    )

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    )

    with pytest.raises(ValueError, match="does not support streaming benchmark mode"):
        orchestrator.run(
            BenchmarkRunRequest(
                benchmark_profile="bench",
                dataset_profile="bench_dataset",
                providers=["providers/fake_batch_only"],
                benchmark_settings={"execution_mode": "streaming", "streaming": {"chunk_ms": 250}},
                run_id="bench_streaming_unsupported",
            )
        )


def test_benchmark_orchestrator_rejects_invalid_merged_streaming_settings(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeStreamingProvider(FakeProviderAdapter):
        provider_id = "fake_stream_validation"

    register_provider("fake_stream_validation", FakeStreamingProvider)
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
                "transcript": "stream 8 chunks",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_stream.yaml",
        {"provider_id": "fake_stream_validation", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(configs / "metrics" / "streaming.yaml", {"metrics": ["wer"]})
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_stream"],
            "metric_profiles": ["metrics/streaming"],
            "execution_mode": "streaming",
            "streaming": {"chunk_ms": 250},
        },
    )

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    )

    with pytest.raises(ValueError, match="Benchmark settings validation failed"):
        orchestrator.run(
            BenchmarkRunRequest(
                benchmark_profile="bench",
                dataset_profile="bench_dataset",
                providers=["providers/fake_stream"],
                benchmark_settings={"execution_mode": "streaming", "streaming": {"chunk_ms": 0}},
                run_id="bench_streaming_invalid_chunk",
            )
        )


def test_benchmark_orchestrator_uses_preset_cost_and_omits_streaming_metrics_in_batch_summary(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeCostProvider(FakeProviderAdapter):
        provider_id = "fake_cost_component"

    register_provider("fake_cost_component", FakeCostProvider)
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
                "duration_sec": 30.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_cost.yaml",
        {
            "provider_id": "fake_cost_component",
            "settings": {},
            "ui": {
                "default_model_preset": "standard",
                "model_presets": {
                    "standard": {
                        "label": "Standard",
                        "estimated_cost_usd_per_min": 0.5,
                        "settings": {},
                    }
                },
            },
        },
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(
        configs / "metrics" / "timing.yaml",
        {
            "metrics": [
                "wer",
                "estimated_cost_usd",
                "total_latency_ms",
                "first_partial_latency_ms",
                "partial_count",
            ]
        },
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_cost"],
            "metric_profiles": ["metrics/timing"],
            "execution_mode": "batch",
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
            providers=["providers/fake_cost"],
            run_id="bench_cost_run",
        )
    )

    expected_cost = (float(wav_duration_sec(str(imported_audio))) / 60.0) * 0.5
    assert summary.mean_metrics["estimated_cost_usd"] == pytest.approx(expected_cost)
    assert "first_partial_latency_ms" not in summary.mean_metrics
    assert "partial_count" not in summary.mean_metrics
    summary_payload = json.loads(
        (
            artifacts / "benchmark_runs" / "bench_cost_run" / "reports" / "summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary_payload["cost_metrics"]["estimated_cost_usd"] == pytest.approx(expected_cost)
    assert summary_payload["cost_totals"]["estimated_cost_usd"] == pytest.approx(expected_cost)
    resource_metrics = summary_payload["resource_metrics"]
    if resource_metrics:
        assert resource_metrics["cpu_percent_mean"] >= 0.0
        assert resource_metrics["memory_mb_mean"] >= 0.0
    assert summary_payload["metric_statistics"]["estimated_cost_usd"]["sum"] == pytest.approx(expected_cost)

    csv_text = (
        artifacts / "benchmark_runs" / "bench_cost_run" / "metrics" / "results.csv"
    ).read_text(encoding="utf-8")
    assert "estimated_cost_usd" in csv_text
    assert "quality_word_edits" in csv_text


def test_benchmark_orchestrator_rejects_empty_normalized_reference_for_quality_metrics(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeBenchProvider(FakeProviderAdapter):
        provider_id = "fake_quality_guard"

    register_provider("fake_quality_guard", FakeBenchProvider)
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
                "sample_id": "sample_bad_ref",
                "audio_path": str(imported_audio),
                "transcript": "!!!",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_quality_guard.yaml",
        {
            "provider_id": "fake_quality_guard",
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
    _write_yaml(
        configs / "metrics" / "quality.yaml",
        {"metrics": ["wer", "cer", "sample_accuracy"]},
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_quality_guard"],
            "metric_profiles": ["metrics/quality"],
        },
    )

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    )

    with pytest.raises(
        ValueError,
        match="Benchmark quality metrics require non-empty normalized reference transcripts",
    ):
        orchestrator.run(
            BenchmarkRunRequest(
                benchmark_profile="bench",
                dataset_profile="bench_dataset",
                providers=["providers/fake_quality_guard"],
                run_id="bench_bad_ref_run",
            )
        )


def test_benchmark_orchestrator_honors_profile_execution_mode_without_request_override(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeStreamingProfileProvider(FakeProviderAdapter):
        provider_id = "fake_stream_profile"

    register_provider("fake_stream_profile", FakeStreamingProfileProvider)
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
                "transcript": "stream 8 chunks",
                "language": "en-US",
                "split": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    _write_yaml(
        configs / "providers" / "fake_stream.yaml",
        {"provider_id": "fake_stream_profile", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(
        configs / "metrics" / "streaming.yaml",
        {"metrics": ["wer", "partial_count", "first_partial_latency_ms"]},
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_stream"],
            "metric_profiles": ["metrics/streaming"],
            "execution_mode": "streaming",
            "streaming": {"chunk_ms": 250},
        },
    )

    summary = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    ).run(
        BenchmarkRunRequest(
            benchmark_profile="bench",
            dataset_profile="bench_dataset",
            providers=["providers/fake_stream"],
            run_id="bench_streaming_from_profile",
        )
    )

    assert summary.metadata["execution_mode"] == "streaming"
    assert summary.mean_metrics["partial_count"] > 0


def test_benchmark_orchestrator_respects_artifact_save_flags(
    tmp_path: Path,
    sample_wav: str,
) -> None:
    class FakeArtifactToggleProvider(FakeProviderAdapter):
        provider_id = "fake_artifact_toggle"

    register_provider("fake_artifact_toggle", FakeArtifactToggleProvider)
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
        configs / "providers" / "fake_artifact_toggle.yaml",
        {"provider_id": "fake_artifact_toggle", "settings": {}},
    )
    _write_yaml(
        configs / "datasets" / "bench_dataset.yaml",
        {"dataset_id": "bench_dataset", "manifest_path": str(manifest_path)},
    )
    _write_yaml(
        configs / "metrics" / "quality.yaml",
        {"metrics": ["wer"]},
    )
    _write_yaml(
        configs / "benchmark" / "bench.yaml",
        {
            "dataset_profile": "datasets/bench_dataset",
            "providers": ["providers/fake_artifact_toggle"],
            "metric_profiles": ["metrics/quality"],
            "save_raw_outputs": False,
            "save_normalized_outputs": False,
        },
    )

    summary = BenchmarkOrchestrator(
        configs_root=str(configs),
        artifact_root=str(artifacts),
        registry_path=str(registry),
    ).run(
        BenchmarkRunRequest(
            benchmark_profile="bench",
            dataset_profile="bench_dataset",
            providers=["providers/fake_artifact_toggle"],
            run_id="bench_artifact_toggle",
        )
    )

    run_dir = artifacts / "benchmark_runs" / summary.run_id
    assert list((run_dir / "raw_outputs").iterdir()) == []
    assert list((run_dir / "normalized_outputs").iterdir()) == []
    assert (run_dir / "metrics" / "results.json").exists()
