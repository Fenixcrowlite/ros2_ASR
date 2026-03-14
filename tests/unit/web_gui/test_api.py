from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

import web_gui.app.main as gui_main
from web_gui.app.aws_auth_store import AwsAuthContext, auth_profile_path
from web_gui.app.command_builder import CommandSpec
from web_gui.app.job_manager import JobManager, JobRecord
from web_gui.app.main import app


def test_api_options_and_files() -> None:
    with TestClient(app) as client:
        options = client.get("/api/options")
        assert options.status_code == 200
        assert "backends" in options.json()

        files = client.get("/api/files")
        assert files.status_code == 200
        payload = files.json()
        assert "uploads" in payload and "results" in payload


def test_api_live_job_start_with_monkeypatched_builder(monkeypatch) -> None:
    monkeypatch.setattr(gui_main, "JOBS", JobManager())

    def fake_build_runtime_config(**_: object):
        return Path("configs/default.yaml"), {"ok": True}, {}

    def fake_live_command(_runtime: Path, _payload: dict[str, object]) -> CommandSpec:
        return CommandSpec(
            shell_command="echo api-live-run",
            display_command="echo api-live-run",
            metadata={},
        )

    monkeypatch.setattr(gui_main, "build_runtime_config", fake_build_runtime_config)
    monkeypatch.setattr(gui_main, "build_live_sample_command", fake_live_command)

    with TestClient(app) as client:
        response = client.post(
            "/api/jobs/live-sample",
            json={
                "profile_name": "test",
                "base_config": "configs/default.yaml",
                "runtime_overrides": {},
                "payload": {"interfaces": "core", "model_runs": "mock"},
                "secrets": {},
            },
        )
        assert response.status_code == 200
        job_id = response.json()["job"]["job_id"]

        deadline = time.time() + 5
        while time.time() < deadline:
            item = client.get(f"/api/jobs/{job_id}")
            status = item.json()["job"]["status"]
            if status != "running":
                break
            time.sleep(0.1)

        logs = client.get(f"/api/jobs/{job_id}/logs")
        assert logs.status_code == 200
        assert "api-live-run" in logs.json()["log"]


def test_api_artifacts_allows_docs_file() -> None:
    with TestClient(app) as client:
        response = client.get("/api/artifacts", params={"path": "docs/run_guide.md"})
        assert response.status_code == 200
        assert "Практическая инструкция" in response.text


def test_api_aws_auth_profile_save_and_load() -> None:
    name = f"unit_auth_{uuid.uuid4().hex[:8]}"
    path = auth_profile_path(name)
    if path.exists():
        path.unlink()
    try:
        with TestClient(app) as client:
            save_response = client.post(
                "/api/aws-auth-profiles",
                json={
                    "name": name,
                    "content": (
                        "AWS_AUTH_TYPE=sso\n"
                        "AWS_PROFILE=ros2ws\n"
                        "AWS_REGION=eu-north-1\n"
                        "AWS_SSO_START_URL=https://d-example.awsapps.com/start\n"
                        "AWS_SSO_REGION=eu-north-1\n"
                    ),
                },
            )
            assert save_response.status_code == 200

            load_response = client.get(f"/api/aws-auth-profiles/{name}")
            assert load_response.status_code == 200
            payload = load_response.json()
            assert payload["values"]["AWS_PROFILE"] == "ros2ws"
            assert payload["values"]["AWS_REGION"] == "eu-north-1"
    finally:
        if path.exists():
            path.unlink()


def test_api_aws_sso_login_starts_job(monkeypatch) -> None:
    monkeypatch.setattr(gui_main, "JOBS", JobManager())

    def fake_resolve_auth_context(name: str, for_login: bool = False) -> AwsAuthContext:
        return AwsAuthContext(
            name=name,
            content=(
                "AWS_PROFILE=ros2ws\n"
                "AWS_REGION=eu-north-1\n"
                "AWS_SSO_START_URL=https://d-example.awsapps.com/start\n"
                "AWS_SSO_REGION=eu-north-1\n"
            ),
            values={
                "AWS_PROFILE": "ros2ws",
                "AWS_REGION": "eu-north-1",
                "AWS_SSO_START_URL": "https://d-example.awsapps.com/start",
                "AWS_SSO_REGION": "eu-north-1",
            },
            runtime_secrets={"aws_profile": "ros2ws", "aws_region": "eu-north-1"},
            env_extra={"AWS_PROFILE": "ros2ws", "AWS_REGION": "eu-north-1"},
            profile_name="ros2ws",
        )

    monkeypatch.setattr(gui_main, "resolve_auth_context", fake_resolve_auth_context)

    with TestClient(app) as client:
        response = client.post(
            "/api/aws-sso-login",
            json={"auth_profile": "demo", "use_device_code": False, "no_browser": True},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["job"]["kind"] == "aws_sso_login"
        assert "--no-browser" in payload["job"]["display_command"]
        assert "--use-device-code" not in payload["job"]["display_command"]


def test_api_aws_sso_login_default_flags_use_device_code_without_no_browser(monkeypatch) -> None:
    monkeypatch.setattr(gui_main, "JOBS", JobManager())

    def fake_resolve_auth_context(name: str, for_login: bool = False) -> AwsAuthContext:
        return AwsAuthContext(
            name=name,
            content=(
                "AWS_PROFILE=ros2ws\n"
                "AWS_REGION=eu-north-1\n"
                "AWS_SSO_START_URL=https://d-example.awsapps.com/start\n"
                "AWS_SSO_REGION=eu-north-1\n"
            ),
            values={
                "AWS_PROFILE": "ros2ws",
                "AWS_REGION": "eu-north-1",
                "AWS_SSO_START_URL": "https://d-example.awsapps.com/start",
                "AWS_SSO_REGION": "eu-north-1",
            },
            runtime_secrets={"aws_profile": "ros2ws", "aws_region": "eu-north-1"},
            env_extra={"AWS_PROFILE": "ros2ws", "AWS_REGION": "eu-north-1"},
            profile_name="ros2ws",
        )

    monkeypatch.setattr(gui_main, "resolve_auth_context", fake_resolve_auth_context)

    with TestClient(app) as client:
        response = client.post("/api/aws-sso-login", json={"auth_profile": "demo"})
        assert response.status_code == 200
        payload = response.json()
        assert "--use-device-code" in payload["job"]["display_command"]
        assert "--no-browser" not in payload["job"]["display_command"]


def test_api_live_job_rejects_aws_without_credentials() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs/live-sample",
            json={
                "profile_name": "aws-negative",
                "base_config": "configs/default.yaml",
                "runtime_overrides": {
                    "asr": {"backend": "aws"},
                    "backends": {"aws": {"s3_bucket": "unit-test-bucket"}},
                },
                "payload": {"interfaces": "core", "model_runs": "aws:transcribe"},
                "secrets": {},
            },
        )
        assert response.status_code == 400
        assert "AWS backend selected but credentials are missing" in response.json()["detail"]


def test_api_jobs_can_hide_inactive_restored(monkeypatch, tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    manager = JobManager(logs_dir=logs_dir, state_path=logs_dir / "jobs_state.json")
    monkeypatch.setattr(gui_main, "JOBS", manager)

    restored_job = JobRecord(
        job_id="restored00001",
        kind="benchmark",
        status="succeeded",
        created_at="2026-03-10T09:00:00",
        started_at="2026-03-10T09:00:00",
        ended_at="2026-03-10T09:01:00",
        metadata={"restored": True},
    )
    current_job = JobRecord(
        job_id="current000001",
        kind="live_sample",
        status="succeeded",
        created_at="2026-03-12T09:00:00",
        started_at="2026-03-12T09:00:00",
        ended_at="2026-03-12T09:01:00",
        metadata={},
    )
    manager._jobs = {  # noqa: SLF001
        restored_job.job_id: restored_job,
        current_job.job_id: current_job,
    }

    with TestClient(app) as client:
        all_jobs = client.get("/api/jobs")
        assert all_jobs.status_code == 200
        all_ids = {item["job_id"] for item in all_jobs.json()["jobs"]}
        assert {"restored00001", "current000001"} <= all_ids

        visible_jobs = client.get("/api/jobs", params={"hide_inactive_restored": True})
        assert visible_jobs.status_code == 200
        visible_ids = {item["job_id"] for item in visible_jobs.json()["jobs"]}
        assert "restored00001" not in visible_ids
        assert "current000001" in visible_ids
