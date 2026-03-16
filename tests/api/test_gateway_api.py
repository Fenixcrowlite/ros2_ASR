from __future__ import annotations

import importlib
import json
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
            "provider_preset": "accurate",
            "provider_settings": {"beam_size": 5},
            "processing_mode": "provider_stream",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    live = client.get("/api/runtime/live").json()
    assert live["status"]["session_state"] == "active"
    assert live["recent_events"][0]["event"] == "runtime_start"
    assert live["status"]["model"] == "accurate"
    assert live["status"]["processing_mode"] == "provider_stream"
    assert live["status"]["streaming_mode"] == "native"

    recognize = client.post(
        "/api/runtime/recognize_once",
        json={
            "wav_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "session_id": session_id,
            "provider_profile": "providers/whisper_local",
            "provider_preset": "light",
            "provider_settings": {"compute_type": "int8"},
        },
    )
    assert recognize.status_code == 200
    assert "recognized from vosk_test.wav" in recognize.json()["text"]
    assert recognize.json()["provider_preset"] == "light"

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
            "audio_file_path": "data/sample/vosk_test.wav",
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
            "audio_file_path": "data/sample/vosk_test.wav",
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
            "scenario": "noise_robustness",
            "provider_overrides": {
                "providers/whisper_local": {
                    "provider_preset": "accurate",
                    "provider_settings": {"beam_size": 4},
                }
            },
            "benchmark_settings": {
                "execution_mode": "streaming",
                "streaming": {"chunk_ms": 250},
                "noise": {"mode": "white", "levels": ["clean", "light"]},
            },
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
    live_row = next(row for row in history["runs"] if row["run_id"] == "bench_live_run")
    assert live_row["scenario"] == "noise_robustness"
    assert live_row["execution_mode"] == "streaming"
    assert "wer" in live_row["quality_metrics"]
    assert "real_time_factor" in live_row["resource_metrics"]

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
    assert isinstance(azure["validation"]["valid"], bool)
    assert "runtime_ready" in (azure["validation"].get("auth") or {})

    logs = client.get("/api/logs?component=runtime&severity=all&limit=10")
    assert logs.status_code == 200
    assert any("sample error" in item["message"] for item in logs.json()["entries"])

    diagnostics = client.get("/api/diagnostics/issues")
    assert diagnostics.status_code == 200
    diag_payload = diagnostics.json()
    assert "counts" in diag_payload
    assert isinstance(diag_payload["counts"].get("warning", 0), int)


def test_azure_env_save_updates_secret_validation_and_local_env(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    save = client.post(
        "/api/secrets/azure_env",
        json={
            "ref_name": "azure_speech_key",
            "speech_key": "azure-test-key",
            "region": "eastus",
            "endpoint": "https://eastus.api.cognitive.microsoft.com/",
        },
    )
    assert save.status_code == 200
    payload = save.json()
    assert payload["validation"]["valid"] is True
    assert payload["validation"]["auth"]["runtime_ready"] is True
    assert payload["validation"]["auth"]["region"] == "eastus"
    assert payload["validation"]["auth"]["speech_key_source"] == "local_env_file"

    env_file = project_root / "secrets" / "local" / "runtime.env"
    assert env_file.exists()
    env_text = env_file.read_text(encoding="utf-8")
    assert "AZURE_SPEECH_KEY=azure-test-key" in env_text
    assert "AZURE_SPEECH_REGION=eastus" in env_text

    status = client.get("/api/secrets/azure_env")
    assert status.status_code == 200
    assert status.json()["auth"]["runtime_ready"] is True

    clear = client.post(
        "/api/secrets/azure_env",
        json={
            "ref_name": "azure_speech_key",
            "clear_speech_key": True,
            "clear_region": True,
            "clear_endpoint": True,
        },
    )
    assert clear.status_code == 200
    assert clear.json()["validation"]["valid"] is False


def test_google_service_account_upload_and_clear(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)

    upload = client.post(
        "/api/secrets/google_service_account/upload",
        data={"ref_name": "google_service_account"},
        files={
            "file": (
                "service-account.json",
                json.dumps(
                    {
                        "type": "service_account",
                        "project_id": "demo-project",
                        "private_key": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
                        "client_email": "demo-account@demo-project.iam.gserviceaccount.com",
                    }
                ).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    assert payload["validation"]["valid"] is True
    assert payload["validation"]["auth"]["runtime_ready"] is True
    assert payload["validation"]["auth"]["project_id"] == "demo-project"

    stored = project_root / "secrets" / "google" / "service-account.json"
    assert stored.exists()

    status = client.get("/api/secrets/google_service_account")
    assert status.status_code == 200
    assert status.json()["auth"]["runtime_ready"] is True

    cleared = client.post("/api/secrets/google_service_account/clear", json={"ref_name": "google_service_account"})
    assert cleared.status_code == 200
    assert cleared.json()["validation"]["valid"] is False
    assert stored.exists() is False


def test_secrets_refs_expose_structured_aws_auth_state(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    class _FakeAwsBackend:
        def auth_status(self):
            return {
                "profile": "ros2ws",
                "region": "eu-north-1",
                "uses_sso": True,
                "runtime_ready": True,
                "login_supported": True,
                "login_recommended": False,
                "status": "role_credentials_valid_sso_expired",
                "message": "Role credentials still work, but the SSO sign-in session is expired.",
                "sso_session_expires_at": "2026-03-16T08:00:00Z",
                "sso_session_valid": False,
                "role_credentials_expires_at": "2026-03-16T20:00:00Z",
                "role_credentials_valid": True,
                "login_command": "aws sso login --profile ros2ws",
            }

        def auth_validation_errors(self):
            return []

    monkeypatch.setattr(gateway_api, "_aws_backend_from_current_env", lambda: _FakeAwsBackend())

    response = client.get("/api/secrets/refs")

    assert response.status_code == 200
    refs = response.json()["refs"]
    aws = next(item for item in refs if item["name"] == "aws_profile")
    assert aws["validation"]["valid"] is True
    assert aws["validation"]["auth"]["status"] == "role_credentials_valid_sso_expired"
    assert aws["validation"]["auth"]["role_credentials_valid"] is True
    assert aws["validation"]["auth"]["sso_session_valid"] is False
    assert aws["validation"]["auth"]["login_supported"] is True


def test_secrets_aws_sso_login_endpoints(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    gateway_api, _fake_ros, client, _project_root = _make_client(repo_root, tmp_path, monkeypatch)

    def _fake_start_aws_login_job(**kwargs):
        return {
            "job_id": "job_aws_login_demo",
            "kind": "aws_sso_login",
            "provider": "aws",
            "ref_name": kwargs["ref_name"],
            "profile": kwargs["profile"],
            "state": "running",
            "started_at": "2026-03-16T10:00:00Z",
            "completed_at": "",
            "return_code": None,
            "lines": ["Open the following URL in your browser"],
            "command": ["aws", "sso", "login", "--profile", kwargs["profile"], "--no-browser", "--use-device-code"],
            "validation": {},
        }

    monkeypatch.setattr(gateway_api, "_start_aws_login_job", _fake_start_aws_login_job)
    class _FakeProcess:
        def __init__(self):
            self._terminated = False

        def poll(self):
            return 0 if self._terminated else None

        def terminate(self):
            self._terminated = True

    fake_process = _FakeProcess()

    gateway_api._SECRET_LOGIN_JOBS["job_aws_login_demo"] = {
        "job_id": "job_aws_login_demo",
        "kind": "aws_sso_login",
        "provider": "aws",
        "ref_name": "aws_profile",
        "profile": "ros2ws",
        "state": "running",
        "started_at": "2026-03-16T10:00:00Z",
        "completed_at": "",
        "return_code": None,
        "lines": ["Open the following URL in your browser"],
        "command": ["aws", "sso", "login", "--profile", "ros2ws", "--no-browser", "--use-device-code"],
        "validation": {},
        "_process": fake_process,
    }

    start = client.post(
        "/api/secrets/aws_sso_login",
        json={
            "ref_name": "aws_profile",
            "profile": "ros2ws",
            "use_device_code": True,
            "no_browser": True,
        },
    )
    assert start.status_code == 200
    assert start.json()["job"]["kind"] == "aws_sso_login"
    assert start.json()["job"]["profile"] == "ros2ws"

    status = client.get("/api/secrets/aws_sso_login/job_aws_login_demo")
    assert status.status_code == 200
    assert status.json()["job"]["state"] == "running"
    assert "browser" in status.json()["job"]["lines"][0].lower()

    cancel = client.post("/api/secrets/aws_sso_login/job_aws_login_demo/cancel", json={})
    assert cancel.status_code == 200
    assert cancel.json()["job"]["state"] == "cancelled"
    assert fake_process._terminated is True


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

        def resolve_profile_payload(self, provider_profile: str):
            return {"provider_id": provider_profile.split("/")[-1]}

        def create_from_profile(
            self,
            provider_profile: str,
            *,
            preset_id: str = "",
            settings_overrides: dict | None = None,
        ):
            del provider_profile, preset_id, settings_overrides
            raise ValueError("Provider config validation failed: AWS SSO token expired")

    monkeypatch.setattr(gateway_api, "ProviderManager", _RejectingManager)

    response = client.post(
        "/api/runtime/start",
        json={
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/aws_cloud",
            "session_id": "",
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
            "mic_capture_sec": 4.0,
        },
    )

    assert response.status_code == 400
    assert "AWS SSO token expired" in response.json()["detail"]
    assert fake_ros.runtime_started is False


def test_dataset_import_upload_registers_manifest(repo_root: Path, tmp_path: Path, monkeypatch) -> None:
    _gateway_api, _fake_ros, client, project_root = _make_client(repo_root, tmp_path, monkeypatch)
    sample_wav = repo_root / "data" / "sample" / "vosk_test.wav"

    response = client.post(
        "/api/datasets/import_upload",
        data={
            "dataset_id": "upload_demo",
            "dataset_profile": "upload_demo",
            "language": "en-US",
        },
        files=[
            ("files", ("vosk_test.wav", sample_wav.read_bytes(), "audio/wav")),
            ("files", ("vosk_test.txt", b"10001 90210 01803\n", "text/plain")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == "upload_demo"
    manifest_path = project_root / "datasets" / "manifests" / "upload_demo.jsonl"
    assert manifest_path.exists()
    datasets = client.get("/api/datasets").json()
    assert "upload_demo" in datasets["dataset_ids"]
