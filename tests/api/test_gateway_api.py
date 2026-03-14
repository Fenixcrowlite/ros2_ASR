from __future__ import annotations

import importlib
import time
from pathlib import Path

from fastapi.testclient import TestClient
from tests.utils.fakes import FakeGatewayRosClient, build_stub_provider_manager
from tests.utils.project import clone_project_layout, seed_benchmark_run, seed_logs


def _make_client(repo_root: Path, tmp_path: Path, monkeypatch):
    project_root = clone_project_layout(repo_root, tmp_path / "project")
    seed_logs(project_root)
    seed_benchmark_run(project_root, "bench_seed_a", wer=0.0, cer=0.0)
    seed_benchmark_run(project_root, "bench_seed_b", wer=0.2, cer=0.1)

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
    return gateway_api, fake_ros, TestClient(gateway_api.app), project_root


def test_runtime_api_round_trip(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/en_hello.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    live = client.get("/api/runtime/live").json()
    assert live["status"]["session_state"] == "active"
    assert live["recent_events"][0]["event"] == "runtime_start"

    recognize = client.post(
        "/api/runtime/recognize_once",
        json={
            "wav_path": "data/sample/en_hello.wav",
            "language": "en-US",
            "session_id": session_id,
            "provider_profile": "providers/whisper_local",
        },
    )
    assert recognize.status_code == 200
    assert "recognized from en_hello.wav" in recognize.json()["text"]

    live_after = client.get("/api/runtime/live").json()
    assert live_after["recent_results"][0]["request_id"] == "req_demo"
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["runtime_live"]["recent_results"][0]["request_id"] == "req_demo"

    stop = client.post("/api/runtime/stop", json={"session_id": session_id})
    assert stop.status_code == 200
    assert client.get("/api/runtime/status").json()["session_state"] == "idle"


def test_runtime_api_rejects_double_start(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    first = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/en_hello.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )
    second = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/en_hello.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already active" in second.json()["detail"]


def test_benchmark_history_status_compare_and_export(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    run = client.post(
        "/api/benchmark/run",
        json={
            "benchmark_profile": "default_benchmark",
            "dataset_profile": "sample_dataset",
            "providers": ["providers/whisper_local"],
            "run_id": "bench_live_run",
        },
    )
    assert run.status_code == 200

    deadline = time.time() + 5.0
    while time.time() < deadline:
        status = client.get("/api/benchmark/status/bench_live_run")
        if status.status_code == 200 and status.json()["state"] == "completed":
            break
        time.sleep(0.05)
    else:
        raise AssertionError("benchmark run did not complete in time")

    history = client.get("/api/benchmark/history").json()
    assert any(row["run_id"] == "bench_live_run" for row in history["runs"])

    compare = client.post("/api/results/compare", json={"run_ids": ["bench_seed_a", "bench_seed_b"]})
    assert compare.status_code == 200
    assert compare.json()["table"]

    export = client.post(
        "/api/results/export",
        json={"run_ids": ["bench_seed_a", "bench_seed_b"], "formats": ["json", "csv", "md"], "name": "compare_demo"},
    )
    assert export.status_code == 200
    outputs = export.json()["outputs"]
    assert (project_root / "artifacts" / "exports" / "compare_demo").exists()
    assert outputs["json"].endswith("comparison.json")


def test_datasets_secrets_logs_and_results_endpoints(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    datasets = client.get("/api/datasets")
    assert datasets.status_code == 200
    assert "sample_dataset" in datasets.json()["dataset_ids"]

    manifest_check = client.post(
        "/api/datasets/validate_manifest",
        json={"manifest_path": str(project_root / "datasets" / "manifests" / "sample_dataset.jsonl"), "check_audio_files": False},
    )
    assert manifest_check.status_code == 200
    assert manifest_check.json()["sample_count"] >= 1

    secrets = client.get("/api/secrets/refs")
    assert secrets.status_code == 200
    refs = secrets.json()["refs"]
    azure = next(item for item in refs if item["name"] == "azure_speech_key")
    assert azure["validation"]["masked"] is True
    assert azure["validation"]["kind"] == "env"
    assert "AZURE_SPEECH_KEY" in azure["validation"]["env"]
    assert azure["validation"]["valid"] is False

    logs = client.get("/api/logs?component=runtime&severity=all&limit=10")
    assert logs.status_code == 200
    assert any("sample error" in item["message"] for item in logs.json()["entries"])

    diagnostics = client.get("/api/diagnostics/issues")
    assert diagnostics.status_code == 200
    assert diagnostics.json()["counts"]["warning"] >= 1


def test_provider_test_returns_bad_request_for_missing_wav(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    response = client.post(
        "/api/providers/test",
        json={"provider_profile": "whisper_local", "wav_path": "missing.wav", "language": "en-US"},
    )

    assert response.status_code == 400
    assert "WAV file not found" in response.json()["detail"]


def test_runtime_start_rejects_invalid_provider_preflight(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _RejectingManager:
        def __init__(self, configs_root: str = "configs") -> None:
            self.configs_root = configs_root

        def create_from_profile(self, provider_profile: str):
            raise ValueError("Provider config validation failed: AWS SSO token expired")

    monkeypatch.setattr(gateway_api, "ProviderManager", _RejectingManager)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/aws_cloud",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/en_zero.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )

    assert response.status_code == 400
    assert "AWS SSO token expired" in response.json()["detail"]
    assert fake_ros.runtime_started is False
