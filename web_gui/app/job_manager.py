"""Background process manager for Web GUI jobs."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from web_gui.app.command_builder import CommandSpec
from web_gui.app.paths import LOGS_DIR


@dataclass(slots=True)
class JobRecord:
    """Tracked process job metadata."""

    job_id: str
    kind: str
    status: str
    created_at: str
    started_at: str
    ended_at: str = ""
    return_code: int | None = None
    shell_command: str = ""
    display_command: str = ""
    log_path: str = ""
    pid: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize record for API responses."""
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "return_code": self.return_code,
            "shell_command": self.shell_command,
            "display_command": self.display_command,
            "log_path": self.log_path,
            "pid": self.pid,
            "metadata": self.metadata,
            "artifacts": self.artifacts,
            "error": self.error,
        }


class JobManager:
    """Thread-safe subprocess manager."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._procs: dict[str, subprocess.Popen[str]] = {}
        self._bash_path = shutil.which("bash") or "/bin/bash"

    def start_job(
        self,
        *,
        kind: str,
        command: CommandSpec,
        env_extra: dict[str, str] | None = None,
        long_running: bool = False,
    ) -> JobRecord:
        """Start subprocess job and begin asynchronous status tracking."""
        now = datetime.now().isoformat(timespec="seconds")
        job_id = uuid.uuid4().hex[:12]
        log_path = LOGS_DIR / f"{now.replace(':', '').replace('-', '')}_{job_id}_{kind}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        for key, value in (env_extra or {}).items():
            if value:
                env[key] = value

        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"[web-gui] kind={kind}\n")
            log_file.write(f"[web-gui] started_at={now}\n")
            log_file.write(f"[web-gui] command={command.display_command}\n\n")

        stdout_handle = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen(
            [self._bash_path, "-lc", command.shell_command],
            stdout=stdout_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
            env=env,
        )

        record = JobRecord(
            job_id=job_id,
            kind=kind,
            status="running",
            created_at=now,
            started_at=now,
            shell_command=command.shell_command,
            display_command=command.display_command,
            log_path=str(log_path),
            pid=process.pid,
            metadata=dict(command.metadata),
        )

        with self._lock:
            self._jobs[job_id] = record
            self._procs[job_id] = process

        monitor = threading.Thread(
            target=self._monitor_job,
            args=(job_id, process, stdout_handle, long_running),
            daemon=True,
        )
        monitor.start()
        return record

    def _monitor_job(
        self,
        job_id: str,
        process: subprocess.Popen[str],
        stdout_handle: Any,
        _: bool,
    ) -> None:
        return_code = process.wait()
        stdout_handle.close()
        ended = datetime.now().isoformat(timespec="seconds")

        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            record.return_code = return_code
            record.ended_at = ended
            if record.status == "stopped":
                pass
            elif return_code == 0:
                record.status = "succeeded"
            else:
                record.status = "failed"

            record.artifacts = self._discover_artifacts(record)
            self._procs.pop(job_id, None)

    def stop_job(self, job_id: str) -> JobRecord:
        """Stop running job by id."""
        with self._lock:
            record = self._jobs.get(job_id)
            process = self._procs.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job: {job_id}")
        if process is None or process.poll() is not None:
            return record

        try:
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=8)
        except Exception:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            except Exception as exc:
                with self._lock:
                    record.error = str(exc)

        with self._lock:
            record.status = "stopped"
            record.ended_at = datetime.now().isoformat(timespec="seconds")
            record.return_code = process.returncode
            record.artifacts = self._discover_artifacts(record)
            self._procs.pop(job_id, None)
        return record

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job: {job_id}")
        return record

    def list_jobs(self) -> list[JobRecord]:
        with self._lock:
            rows = list(self._jobs.values())
        return sorted(rows, key=lambda item: item.started_at, reverse=True)

    def read_log_tail(self, job_id: str, *, lines: int = 300) -> str:
        """Read last N lines from job log."""
        record = self.get_job(job_id)
        path = Path(record.log_path)
        if not path.exists():
            return ""
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            content = fh.readlines()
        return "".join(content[-max(lines, 1) :])

    @staticmethod
    def _discover_artifacts(record: JobRecord) -> list[str]:
        artifacts: list[str] = []
        for key in ["runtime_config", "output_json", "output_csv", "report"]:
            value = record.metadata.get(key)
            if not value:
                continue
            path = Path(str(value))
            if path.exists():
                artifacts.append(str(path.resolve()))

        run_dir = Path(str(record.metadata.get("run_dir", "")))
        if run_dir.exists():
            for pattern in ["*.json", "*.csv", "*.md", "plots/*.png"]:
                for candidate in run_dir.glob(pattern):
                    artifacts.append(str(candidate.resolve()))

        output_dir = Path(str(record.metadata.get("output_dir", "")))
        if output_dir.exists():
            subdirs = [item for item in output_dir.iterdir() if item.is_dir()]
            if subdirs:
                latest = sorted(subdirs)[-1]
                for pattern in ["*.json", "*.csv", "*.md", "*.wav", "plots/*.png"]:
                    for candidate in latest.glob(pattern):
                        artifacts.append(str(candidate.resolve()))

        unique: list[str] = []
        seen: set[str] = set()
        for artifact_path in artifacts:
            if artifact_path in seen:
                continue
            seen.add(artifact_path)
            unique.append(artifact_path)
        return unique
