from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from asr_provider_base import ProviderManager, register_provider

from tests.utils.fakes import FakeProviderAdapter


class AdapterPathProvider(FakeProviderAdapter):
    provider_id = "fake_adapter_path"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_provider_manager_creates_provider_from_profile_with_secret_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLocalComponentProvider(FakeProviderAdapter):
        provider_id = "fake_local_component"

    register_provider("fake_local_component", FakeLocalComponentProvider)
    configs = tmp_path / "configs"
    secrets = tmp_path / "secrets" / "refs"

    _write_yaml(
        configs / "providers" / "fake_local.yaml",
        {
            "provider_id": "fake_local_component",
            "settings": {"temperature": 0.0},
            "credentials_ref": "secrets/refs/local_env.yaml",
        },
    )
    _write_yaml(
        secrets / "local_env.yaml",
        {
            "ref_id": "secrets/fake_local",
            "provider": "fake_local_component",
            "kind": "env",
            "required": ["FAKE_LOCAL_TOKEN"],
        },
    )
    monkeypatch.setenv("FAKE_LOCAL_TOKEN", "token-123456")

    manager = ProviderManager(configs_root=str(configs))
    provider = manager.create_from_profile("providers/fake_local")

    assert provider.provider_id == "fake_local_component"
    assert provider.get_status().state == "initialized"


def test_provider_manager_raises_for_invalid_provider_config(tmp_path: Path) -> None:
    class FakeInvalidComponentProvider(FakeProviderAdapter):
        provider_id = "fake_invalid_component"

    register_provider("fake_invalid_component", FakeInvalidComponentProvider)
    configs = tmp_path / "configs"

    _write_yaml(
        configs / "providers" / "broken.yaml",
        {
            "provider_id": "fake_invalid_component",
            "settings": {"invalid": True},
        },
    )

    manager = ProviderManager(configs_root=str(configs))
    with pytest.raises(ValueError, match="invalid config requested by test fixture"):
        manager.create_from_profile("providers/broken")


def test_provider_manager_rejects_empty_vosk_model_directory(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    empty_model_dir = tmp_path / "models" / "vosk"
    empty_model_dir.mkdir(parents=True, exist_ok=True)
    (empty_model_dir / ".gitkeep").write_text("", encoding="utf-8")

    _write_yaml(
        configs / "providers" / "vosk_local.yaml",
        {
            "provider_id": "vosk",
            "settings": {"model_path": str(empty_model_dir)},
        },
    )

    manager = ProviderManager(configs_root=str(configs))
    with pytest.raises(ValueError, match="does not contain a Vosk model"):
        manager.create_from_profile("providers/vosk_local")


def test_provider_manager_rejects_legacy_whisper_cpu_fallback_setting(tmp_path: Path) -> None:
    configs = tmp_path / "configs"

    _write_yaml(
        configs / "providers" / "whisper_local.yaml",
        {
            "provider_id": "whisper",
            "settings": {
                "model_size": "tiny",
                "device": "cuda",
                "compute_type": "float16",
                "allow_cpu_fallback": True,
            },
        },
    )

    manager = ProviderManager(configs_root=str(configs))
    with pytest.raises(ValueError, match="allow_cpu_fallback"):
        manager.create_from_profile("providers/whisper_local")


def test_provider_manager_uses_explicit_adapter_path_without_registry_registration(
    tmp_path: Path,
) -> None:
    configs = tmp_path / "configs"

    _write_yaml(
        configs / "providers" / "adapter_path.yaml",
        {
            "provider_id": "fake_adapter_path",
            "adapter": "tests.component.test_provider_manager.AdapterPathProvider",
            "settings": {"temperature": 0.0},
        },
    )

    manager = ProviderManager(configs_root=str(configs))
    provider = manager.create_from_profile("providers/adapter_path")

    assert provider.provider_id == "fake_adapter_path"
    assert provider.get_status().state == "initialized"
