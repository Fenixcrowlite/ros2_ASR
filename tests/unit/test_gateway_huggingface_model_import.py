from __future__ import annotations

import importlib
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def test_gateway_huggingface_model_import_creates_preset_and_updates_profiles(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_hf_import_seed", wer=0.0, cer=0.0)

    fake_ros = FakeGatewayRosClient(project_root=project_root)
    import asr_gateway.ros_client as ros_client_module

    monkeypatch.setenv("ASR_PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(ros_client_module, "GatewayRosClient", lambda timeout_sec=5.0: fake_ros)
    import asr_gateway.api as gateway_api

    gateway_api = importlib.reload(gateway_api)
    monkeypatch.setattr(
        gateway_api,
        "ProviderManager",
        build_stub_provider_manager(str(project_root / "configs")),
    )

    saved = gateway_api.providers_huggingface_import_model(
        gateway_api.HuggingFaceModelImportRequest(
            provider_profile="providers/huggingface_local",
            model_ref="https://huggingface.co/facebook/wav2vec2-large-960h-lv60-self",
            preset_id="wav2vec2_large",
            label="Wav2Vec2 Large",
            description="Imported directly from the GUI test flow.",
            set_default=False,
            update_base_settings=False,
            settings={"device": "cuda:0", "torch_dtype": "float16"},
        )
    )

    assert saved["saved"] is True
    assert saved["provider_profile"] == "providers/huggingface_local"
    assert saved["provider_profile_id"] == "huggingface_local"
    assert saved["provider_id"] == "huggingface_local"
    assert saved["model_id"] == "facebook/wav2vec2-large-960h-lv60-self"
    assert saved["preset_id"] == "wav2vec2_large"
    assert saved["default_preset"] == "balanced"
    assert saved["execution_preview"]["selected_preset"] == "wav2vec2_large"
    assert (
        saved["execution_preview"]["settings"]["model_id"]
        == "facebook/wav2vec2-large-960h-lv60-self"
    )
    assert saved["execution_preview"]["settings"]["device"] == "cuda:0"
    assert saved["execution_preview"]["settings"]["torch_dtype"] == "float16"
    assert saved["valid"] is True
    assert saved["validation_message"] == "valid"

    profile_path = project_root / "configs" / "providers" / "huggingface_local.yaml"
    profile_payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    preset = profile_payload["ui"]["model_presets"]["wav2vec2_large"]

    assert profile_payload["settings"]["model_id"] == "openai/whisper-small"
    assert profile_payload["ui"]["default_model_preset"] == "balanced"
    assert preset["label"] == "Wav2Vec2 Large"
    assert preset["description"] == "Imported directly from the GUI test flow."
    assert preset["settings"]["model_id"] == "facebook/wav2vec2-large-960h-lv60-self"
    assert preset["settings"]["device"] == "cuda:0"
    assert preset["settings"]["torch_dtype"] == "float16"

    profiles = {
        row["provider_profile"]: row for row in gateway_api.providers_profiles()["profiles"]
    }
    imported_profile = profiles["huggingface_local"]
    imported_presets = {row["preset_id"]: row for row in imported_profile["model_presets"]}

    assert "wav2vec2_large" in imported_presets
    assert imported_presets["wav2vec2_large"]["settings"]["model_id"] == (
        "facebook/wav2vec2-large-960h-lv60-self"
    )
