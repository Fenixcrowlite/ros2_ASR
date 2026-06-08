from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from asr_provider_base import create_provider, list_providers

from tests.utils.fakes import FakeProviderAdapter


class DynamicConfigProvider(FakeProviderAdapter):
    provider_id = "dynamic_config_provider"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_registry_discovers_provider_from_profile_adapter_path(tmp_path: Path) -> None:
    configs_root = tmp_path / "configs"
    _write_yaml(
        configs_root / "providers" / "dynamic_config_provider.yaml",
        {
            "provider_id": "dynamic_config_provider",
            "adapter": "tests.unit.test_provider_plugin_discovery.DynamicConfigProvider",
            "settings": {},
        },
    )

    assert "dynamic_config_provider" in list_providers(configs_root=str(configs_root))

    provider = create_provider("dynamic_config_provider", configs_root=str(configs_root))

    assert provider.provider_id == "dynamic_config_provider"
    assert type(provider).__name__ == "DynamicConfigProvider"


def test_registry_discovers_provider_from_env_plugin(monkeypatch) -> None:
    monkeypatch.setenv(
        "ASR_PROVIDER_PLUGIN_MODULES",
        "env_provider=tests.unit.test_provider_plugin_discovery.DynamicConfigProvider",
    )

    assert "env_provider" in list_providers()

    provider = create_provider("env_provider")

    assert provider.provider_id == "dynamic_config_provider"
    assert type(provider).__name__ == "DynamicConfigProvider"
