from __future__ import annotations

import time

from web_gui.app.command_builder import CommandSpec
from web_gui.app.job_manager import JobManager


def _wait_for_finish(manager: JobManager, job_id: str, timeout_sec: float = 10.0) -> str:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        status = manager.get_job(job_id).status
        if status != "running":
            return status
        time.sleep(0.1)
    raise AssertionError(f"Job {job_id} did not finish in time")


def test_job_manager_runs_short_command() -> None:
    manager = JobManager()
    cmd = CommandSpec(
        shell_command="echo hello-web-gui",
        display_command="echo hello-web-gui",
    )
    record = manager.start_job(kind="unit", command=cmd)
    status = _wait_for_finish(manager, record.job_id)
    assert status == "succeeded"
    log = manager.read_log_tail(record.job_id, lines=50)
    assert "hello-web-gui" in log


def test_job_manager_stops_long_running_job() -> None:
    manager = JobManager()
    cmd = CommandSpec(shell_command="sleep 30", display_command="sleep 30")
    record = manager.start_job(kind="unit_long", command=cmd, long_running=True)
    time.sleep(0.3)
    stopped = manager.stop_job(record.job_id)
    assert stopped.status in {"stopped", "failed", "succeeded"}
