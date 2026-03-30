from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from asr_config.loader import list_profiles, resolve_profile


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_resolve_profile_applies_inheritance_and_override_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configs = tmp_path / "configs"
    _write_yaml(
        configs / "runtime" / "_base.yaml",
        {
            "audio": {"source": "file", "sample_rate_hz": 16000},
            "preprocess": {"normalize": True},
            "vad": {"energy_threshold": 100},
            "orchestrator": {"language": "en-US", "provider_profile": "providers/base"},
        },
    )
    _write_yaml(configs / "deployment" / "dev_local.yaml", {"audio": {"source": "mic"}})
    _write_yaml(
        configs / "runtime" / "parent.yaml",
        {"audio": {"channels": 1}, "orchestrator": {"provider_profile": "providers/parent"}},
    )
    _write_yaml(
        configs / "runtime" / "child.yaml",
        {
            "inherits": ["parent"],
            "audio": {"sample_rate_hz": 22050},
            "orchestrator": {"language": "sk-SK"},
        },
    )

    monkeypatch.setenv("ASR_CFG__audio.source", "env")

    resolved = resolve_profile(
        profile_type="runtime",
        profile_id="child",
        configs_root=str(configs),
        launch_overrides={"audio": {"chunk_ms": 250}},
        env_overrides={"audio": {"source": "mic-env"}},
        ros_param_overrides={"orchestrator": {"provider_profile": "providers/ros"}},
        session_overrides={"audio": {"source": "session"}},
    )

    assert resolved.data["audio"]["sample_rate_hz"] == 22050
    assert resolved.data["audio"]["channels"] == 1
    assert resolved.data["audio"]["chunk_ms"] == 250
    assert resolved.data["audio"]["source"] == "session"
    assert resolved.data["orchestrator"]["provider_profile"] == "providers/ros"
    assert resolved.data["orchestrator"]["language"] == "sk-SK"
    assert Path(resolved.snapshot_path).exists()
    assert resolved.merge_order[0].endswith("runtime/_base.yaml")


def test_resolve_profile_detects_circular_inheritance(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    _write_yaml(configs / "runtime" / "a.yaml", {"inherits": ["b"]})
    _write_yaml(configs / "runtime" / "b.yaml", {"inherits": ["a"]})

    with pytest.raises(ValueError, match="Circular profile inheritance"):
        resolve_profile(
            profile_type="runtime",
            profile_id="a",
            configs_root=str(configs),
            write_snapshot=False,
        )


def test_list_profiles_excludes_base_files(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    _write_yaml(configs / "providers" / "_base.yaml", {"provider_id": "base"})
    _write_yaml(configs / "providers" / "whisper_local.yaml", {"provider_id": "whisper"})
    _write_yaml(configs / "providers" / "azure_cloud.yaml", {"provider_id": "azure"})

    assert list_profiles("providers", configs_root=str(configs)) == ["azure_cloud", "whisper_local"]


def test_env_override_reader_uses_process_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configs = tmp_path / "configs"
    _write_yaml(
        configs / "runtime" / "default_runtime.yaml",
        {
            "audio": {"sample_rate_hz": 16000},
            "preprocess": {"normalize": True},
            "vad": {"energy_threshold": 300},
            "orchestrator": {"provider_profile": "providers/whisper_local"},
        },
    )
    monkeypatch.setenv("ASR_CFG__audio.source", "mic")
    monkeypatch.setenv("ASR_CFG__orchestrator.language", "de-DE")

    resolved = resolve_profile(
        profile_type="runtime",
        profile_id="default_runtime",
        configs_root=str(configs),
        write_snapshot=False,
    )

    assert resolved.data["audio"]["source"] == "mic"
    assert resolved.data["orchestrator"]["language"] == "de-DE"
    assert "ASR_CFG__audio.source" in os.environ


def test_resolve_profile_applies_scoped_deployment_defaults_without_leaking_scaffolding(
    tmp_path: Path,
) -> None:
    configs = tmp_path / "configs"
    _write_yaml(
        configs / "deployment" / "dev_local.yaml",
        {
            "runtime_defaults": {
                "audio": {"source": "mic"},
                "session": {"max_concurrent_sessions": 2},
            },
            "benchmark_defaults": {
                "execution_mode": "streaming",
                "save_raw_outputs": False,
            },
        },
    )
    _write_yaml(
        configs / "runtime" / "default_runtime.yaml",
        {
            "audio": {"sample_rate_hz": 16000, "chunk_ms": 500, "file_path": "demo.wav"},
            "preprocess": {"target_sample_rate_hz": 16000},
            "vad": {"energy_threshold": 100},
            "orchestrator": {"provider_profile": "providers/whisper_local"},
        },
    )
    _write_yaml(
        configs / "benchmark" / "default_benchmark.yaml",
        {
            "dataset_profile": "datasets/sample_dataset",
            "providers": ["providers/whisper_local"],
            "metric_profiles": ["metrics/default_quality"],
        },
    )

    runtime_resolved = resolve_profile(
        profile_type="runtime",
        profile_id="default_runtime",
        configs_root=str(configs),
        write_snapshot=False,
    )
    benchmark_resolved = resolve_profile(
        profile_type="benchmark",
        profile_id="default_benchmark",
        configs_root=str(configs),
        write_snapshot=False,
    )

    assert runtime_resolved.data["audio"]["source"] == "mic"
    assert runtime_resolved.data["session"]["max_concurrent_sessions"] == 2
    assert "runtime_defaults" not in runtime_resolved.data
    assert benchmark_resolved.data["execution_mode"] == "streaming"
    assert benchmark_resolved.data["save_raw_outputs"] is False
    assert "benchmark_defaults" not in benchmark_resolved.data
