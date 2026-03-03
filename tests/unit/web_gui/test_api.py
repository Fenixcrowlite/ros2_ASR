from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

import web_gui.app.main as gui_main
from web_gui.app.command_builder import CommandSpec
from web_gui.app.job_manager import JobManager
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
