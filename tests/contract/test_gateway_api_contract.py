from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient
from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def _load_gateway(repo_root: Path, tmp_path: Path, monkeypatch):
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_contract_a", wer=0.0, cer=0.0)
    seed_benchmark_run(project_root, "bench_contract_b", wer=0.2, cer=0.1)

    fake_ros = FakeGatewayRosClient(project_root=project_root)
    import asr_gateway.ros_client as ros_client_module

    monkeypatch.setenv("ASR_PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(ros_client_module, "GatewayRosClient", lambda timeout_sec=5.0: fake_ros)
    import asr_gateway.api as gateway_api

    gateway_api = importlib.reload(gateway_api)
    monkeypatch.setattr(gateway_api, "ProviderManager", build_stub_provider_manager(str(project_root / "configs")))
    monkeypatch.setattr(
        gateway_api,
        "create_provider",
        lambda provider_id: build_stub_provider_manager(str(project_root / "configs"))().create_from_profile(
            f"providers/{'azure_cloud' if provider_id == 'azure' else 'whisper_local'}"
        ),
    )
    monkeypatch.setattr(gateway_api, "list_providers", lambda: ["whisper", "azure", "aws"])
    gateway_api._RUNTIME_EVENTS.clear()
    gateway_api._RUNTIME_RESULTS.clear()
    gateway_api._BENCHMARK_JOBS.clear()
    return gateway_api, fake_ros


def test_runtime_live_contract(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, fake_ros = _load_gateway(repo_root, tmp_path, monkeypatch)
    client = TestClient(gateway_api.app)

    fake_ros.start_runtime(
        "default_runtime",
        "providers/whisper_local",
        "session_contract",
        audio_source="file",
        audio_file_path="data/sample/vosk_test.wav",
        language="en-US",
        mic_capture_sec=4.0,
    )
    response = client.get("/api/runtime/live")
    payload = response.json()

    assert response.status_code == 200
    assert set(payload.keys()) == {
        "status",
        "recent_events",
        "recent_results",
        "recent_partials",
        "node_statuses",
        "session_statuses",
        "active_session",
        "time",
    }
    assert {"backend", "session_id", "session_state", "capabilities"} <= set(payload["status"].keys())


def test_results_run_detail_contract(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, _fake_ros = _load_gateway(repo_root, tmp_path, monkeypatch)
    client = TestClient(gateway_api.app)

    response = client.get("/api/results/runs/bench_contract_a")
    payload = response.json()

    assert response.status_code == 200
    assert {"run_id", "state", "run_manifest", "summary", "results_head", "results_count", "artifacts"} <= set(payload.keys())
    assert {"manifest", "summary_json", "summary_md", "results_json", "results_csv"} <= set(payload["artifacts"].keys())


def test_dashboard_contract_contains_operator_and_engineering_views(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, _fake_ros = _load_gateway(repo_root, tmp_path, monkeypatch)
    client = TestClient(gateway_api.app)

    response = client.get("/api/dashboard")
    payload = response.json()

    assert response.status_code == 200
    assert {"system", "runtime", "benchmark", "cloud_credentials", "alerts", "quick_actions"} <= set(payload.keys())
    assert {"gateway", "runtime", "benchmark_active", "providers_configured", "providers_invalid"} <= set(payload["system"].keys())
