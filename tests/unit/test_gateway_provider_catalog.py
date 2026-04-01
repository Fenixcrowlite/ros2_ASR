from __future__ import annotations

import importlib
from pathlib import Path

from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def test_gateway_provider_catalog_includes_huggingface_local_and_api(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_catalog_seed", wer=0.0, cer=0.0)

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
    monkeypatch.setattr(
        gateway_api,
        "create_provider",
        lambda provider_id, configs_root=None: build_stub_provider_manager(
            str(project_root / "configs")
        )().create_from_profile(
            {
                "azure": "providers/azure_cloud",
                "aws": "providers/aws_cloud",
                "google": "providers/google_cloud",
                "huggingface_local": "providers/huggingface_local",
                "huggingface_api": "providers/huggingface_api",
            }.get(provider_id, "providers/whisper_local")
        ),
    )
    monkeypatch.setattr(
        gateway_api,
        "list_providers",
        lambda *args, **kwargs: ["huggingface_local", "huggingface_api"],
    )

    providers = {item["provider_id"]: item for item in gateway_api._provider_catalog()}

    assert providers["huggingface_local"]["kind"] == "local"
    assert providers["huggingface_local"]["runtime_ready"] is True
    assert providers["huggingface_local"]["status"] == "ready"
    assert providers["huggingface_api"]["kind"] == "cloud"
    assert providers["huggingface_api"]["capabilities"]["requires_network"] is True
    assert providers["huggingface_api"]["runtime_ready"] is True
    assert providers["huggingface_api"]["status"] == "ready"
