from __future__ import annotations

import subprocess
import time
from pathlib import Path

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


def _new_manager(tmp_path: Path) -> JobManager:
    logs_dir = tmp_path / "logs"
    return JobManager(logs_dir=logs_dir, state_path=logs_dir / "jobs_state.json", history_limit=100)


def test_job_manager_runs_short_command(tmp_path: Path) -> None:
    manager = _new_manager(tmp_path)
    cmd = CommandSpec(
        shell_command="echo hello-web-gui",
        display_command="echo hello-web-gui",
    )
    record = manager.start_job(kind="unit", command=cmd)
    status = _wait_for_finish(manager, record.job_id)
    assert status == "succeeded"
    log = manager.read_log_tail(record.job_id, lines=50)
    assert "hello-web-gui" in log


def test_job_manager_stops_long_running_job(tmp_path: Path) -> None:
    manager = _new_manager(tmp_path)
    cmd = CommandSpec(shell_command="sleep 30", display_command="sleep 30")
    record = manager.start_job(kind="unit_long", command=cmd, long_running=True)
    time.sleep(0.3)
    stopped = manager.stop_job(record.job_id)
    assert stopped.status in {"stopped", "failed", "succeeded"}


def test_job_manager_stop_records_wait_timeout_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manager = _new_manager(tmp_path)
    cmd = CommandSpec(shell_command="sleep 30", display_command="sleep 30")
    record = manager.start_job(kind="unit_long", command=cmd, long_running=True)
    time.sleep(0.3)

    proc = manager._procs[record.job_id]  # noqa: SLF001

    def _fake_wait(*, timeout: float | None = None) -> int:
        raise subprocess.TimeoutExpired(cmd="sleep 30", timeout=timeout or 0.0)

    monkeypatch.setattr(proc, "wait", _fake_wait)
    stopped = manager.stop_job(record.job_id)

    assert stopped.status == "stopped"
    assert "Process wait timeout after stop signal" in stopped.error


def test_job_manager_restores_jobs_from_state_file(tmp_path: Path) -> None:
    manager = _new_manager(tmp_path)
    cmd = CommandSpec(
        shell_command="echo persisted-job",
        display_command="echo persisted-job",
    )
    record = manager.start_job(kind="unit", command=cmd)
    status = _wait_for_finish(manager, record.job_id)
    assert status == "succeeded"

    restored = _new_manager(tmp_path)
    loaded = restored.get_job(record.job_id)
    assert loaded.status == "succeeded"
    assert loaded.metadata.get("restored") is True
    assert "persisted-job" in restored.read_log_tail(record.job_id, lines=50)


def test_job_manager_restores_jobs_from_logs_when_state_missing(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "20260309T154449_deadbeefcafe_ros_bringup.log"
    log_path.write_text(
        "\n".join(
            [
                "[web-gui] kind=ros_bringup",
                "[web-gui] started_at=2026-03-09T15:44:49",
                "[web-gui] command=ros2 launch asr_ros bringup.launch.py config:=demo.yaml",
                "",
                "[INFO] restored from log fallback",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manager = JobManager(
        logs_dir=logs_dir,
        state_path=logs_dir / "jobs_state.json",
        history_limit=100,
    )
    restored = manager.get_job("deadbeefcafe")
    assert restored.kind == "ros_bringup"
    assert restored.status in {"restored", "running"}
    assert restored.metadata.get("restored") is True
    assert "restored from log fallback" in manager.read_log_tail("deadbeefcafe", lines=20)


def test_job_manager_list_jobs_hides_inactive_restored(tmp_path: Path) -> None:
    manager = _new_manager(tmp_path)
    short = CommandSpec(shell_command="echo done", display_command="echo done")
    long = CommandSpec(shell_command="sleep 30", display_command="sleep 30")

    done_job = manager.start_job(kind="short", command=short)
    running_job = manager.start_job(kind="long", command=long, long_running=True)
    status = _wait_for_finish(manager, done_job.job_id)
    assert status == "succeeded"

    # Simulate app restart metadata for historical inactive job.
    manager._jobs[done_job.job_id].metadata["restored"] = True  # noqa: SLF001

    all_jobs = manager.list_jobs()
    visible_jobs = manager.list_jobs(hide_inactive_restored=True)

    all_ids = {item.job_id for item in all_jobs}
    visible_ids = {item.job_id for item in visible_jobs}
    assert done_job.job_id in all_ids
    assert running_job.job_id in all_ids
    assert done_job.job_id not in visible_ids
    assert running_job.job_id in visible_ids

    manager.stop_job(running_job.job_id)


def test_job_manager_list_jobs_keeps_active_restored_visible(tmp_path: Path) -> None:
    manager = _new_manager(tmp_path)
    long = CommandSpec(shell_command="sleep 30", display_command="sleep 30")

    running_job = manager.start_job(kind="long", command=long, long_running=True)
    time.sleep(0.2)

    manager._jobs[running_job.job_id].metadata["restored"] = True  # noqa: SLF001
    manager._jobs[running_job.job_id].status = "running"  # noqa: SLF001

    visible_jobs = manager.list_jobs(hide_inactive_restored=True)
    visible_ids = {item.job_id for item in visible_jobs}
    assert running_job.job_id in visible_ids

    manager.stop_job(running_job.job_id)
