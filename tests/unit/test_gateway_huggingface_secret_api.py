from __future__ import annotations

import importlib
from pathlib import Path

from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def test_gateway_huggingface_token_save_updates_secret_refs_and_dashboard(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_hf_secret_seed", wer=0.0, cer=0.0)

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

    saved = gateway_api.secret_huggingface_token_save(
        gateway_api.HuggingFaceTokenSaveRequest(
            ref_name="huggingface_api_token",
            token="hf_demo_token",
        )
    )

    assert saved["saved"] is True
    assert Path(saved["env_file"]).exists()

    refs = {item["name"]: item for item in gateway_api.secret_refs()["refs"]}
    assert refs["huggingface_api_token"]["validation"]["auth"]["runtime_ready"] is True
    assert refs["huggingface_api_token"]["validation"]["auth"]["status"] == "ready"
    assert refs["huggingface_local_token"]["validation"]["auth"]["runtime_ready"] is True
    assert refs["huggingface_local_token"]["validation"]["auth"]["status"] == "ready"

    cloud_rows = {item["provider"]: item for item in gateway_api._cloud_credential_overview()}
    assert cloud_rows["huggingface_api"]["runtime_ready"] is True
    assert cloud_rows["huggingface_api"]["state"] == "ready"

    cleared = gateway_api.secret_huggingface_token_save(
        gateway_api.HuggingFaceTokenSaveRequest(
            ref_name="huggingface_api_token",
            clear_token=True,
        )
    )

    assert cleared["saved"] is True
    refs_after_clear = {item["name"]: item for item in gateway_api.secret_refs()["refs"]}
    assert refs_after_clear["huggingface_api_token"]["validation"]["auth"]["runtime_ready"] is False
    assert refs_after_clear["huggingface_api_token"]["validation"]["auth"]["status"] == "missing_credentials"
    assert refs_after_clear["huggingface_local_token"]["validation"]["auth"]["runtime_ready"] is True
    assert refs_after_clear["huggingface_local_token"]["validation"]["auth"]["status"] == "optional_missing"
