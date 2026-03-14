"""Background process manager for Web GUI jobs."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from web_gui.app.command_builder import CommandSpec
from web_gui.app.paths import LOGS_DIR

_JOB_LOG_RE = re.compile(
    r"^(?P<stamp>\d{8}T\d{6})_(?P<job_id>[0-9a-fA-F]{12})_(?P<kind>.+)\.log$"
)
ACTIVE_JOB_STATUSES = frozenset({"running"})


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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JobRecord:
        """Deserialize record from persisted JSON payload."""
        job_id = str(payload.get("job_id", "")).strip()
        if not job_id:
            raise ValueError("Missing job_id")

        return cls(
            job_id=job_id,
            kind=str(payload.get("kind", "")).strip() or "unknown",
            status=str(payload.get("status", "")).strip() or "restored",
            created_at=(
                str(payload.get("created_at", "")).strip()
                or str(payload.get("started_at", "")).strip()
                or datetime.now().isoformat(timespec="seconds")
            ),
            started_at=(
                str(payload.get("started_at", "")).strip()
                or str(payload.get("created_at", "")).strip()
                or datetime.now().isoformat(timespec="seconds")
            ),
            ended_at=str(payload.get("ended_at", "")).strip(),
            return_code=_to_optional_int(payload.get("return_code")),
            shell_command=str(payload.get("shell_command", "")).strip(),
            display_command=str(payload.get("display_command", "")).strip(),
            log_path=str(payload.get("log_path", "")).strip(),
            pid=_to_optional_int(payload.get("pid")),
            metadata=dict(payload.get("metadata", {}))
            if isinstance(payload.get("metadata"), dict)
            else {},
            artifacts=[str(item) for item in payload.get("artifacts", [])]
            if isinstance(payload.get("artifacts"), list)
            else [],
            error=str(payload.get("error", "")).strip(),
        )


def _to_optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith("-"):
            candidate = candidate[1:]
        if candidate.isdigit():
            return int(value)
    return None


def _stamp_to_iso(stamp: str) -> str:
    try:
        dt = datetime.strptime(stamp, "%Y%m%dT%H%M%S")
        return dt.isoformat(timespec="seconds")
    except ValueError:
        return stamp


class JobManager:
    """Thread-safe subprocess manager."""

    def __init__(
        self,
        *,
        logs_dir: Path = LOGS_DIR,
        state_path: Path | None = None,
        history_limit: int = 500,
    ) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._procs: dict[str, subprocess.Popen[str]] = {}
        self._logs_dir = logs_dir
        self._state_path = state_path or (self._logs_dir / "jobs_state.json")
        self._history_limit = max(int(history_limit), 50)
        self._bash_path = shutil.which("bash") or "/bin/bash"
        self._restore_state()

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
        log_path = self._logs_dir / f"{now.replace(':', '').replace('-', '')}_{job_id}_{kind}.log"
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
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[web-gui] pid={process.pid}\n\n")

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
            self._enforce_history_limit_locked()
            self._persist_state_locked()

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
            self._enforce_history_limit_locked()
            self._persist_state_locked()

    def stop_job(self, job_id: str) -> JobRecord:
        """Stop running job by id."""
        with self._lock:
            record = self._jobs.get(job_id)
            process = self._procs.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job: {job_id}")
        if process is None or process.poll() is not None:
            if record.status == "running" and self._is_process_alive(record.pid):
                error = self._terminate_process_group(record.pid)
                with self._lock:
                    record.status = "stopped"
                    record.ended_at = datetime.now().isoformat(timespec="seconds")
                    record.return_code = None
                    record.error = error
                    record.artifacts = self._discover_artifacts(record)
                    self._persist_state_locked()
            return record

        error = self._terminate_process_group(process.pid)
        wait_error = ""
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired as exc:
            wait_error = f"Process wait timeout after stop signal: {exc}"

        with self._lock:
            record.status = "stopped"
            record.ended_at = datetime.now().isoformat(timespec="seconds")
            record.return_code = process.returncode
            if error and wait_error:
                record.error = f"{error}; {wait_error}"
            elif error:
                record.error = error
            else:
                record.error = wait_error
            record.artifacts = self._discover_artifacts(record)
            self._procs.pop(job_id, None)
            self._enforce_history_limit_locked()
            self._persist_state_locked()
        return record

    def get_job(self, job_id: str) -> JobRecord:
        self._sync_orphaned_jobs()
        with self._lock:
            record = self._jobs.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job: {job_id}")
        return record

    @staticmethod
    def is_active_status(status: str) -> bool:
        """Return True for statuses considered active in UI/API views."""
        return str(status).strip().lower() in ACTIVE_JOB_STATUSES

    def list_jobs(self, *, hide_inactive_restored: bool = False) -> list[JobRecord]:
        self._sync_orphaned_jobs()
        with self._lock:
            rows = list(self._jobs.values())
        if hide_inactive_restored:
            rows = [
                row
                for row in rows
                if not (
                    bool(row.metadata.get("restored"))
                    and not self.is_active_status(row.status)
                )
            ]
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

    @staticmethod
    def _is_process_alive(pid: int | None) -> bool:
        if pid is None or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def _terminate_process_group(self, pid: int | None) -> str:
        if pid is None or pid <= 0:
            return "Process PID is missing"

        try:
            os.killpg(pid, signal.SIGINT)
        except ProcessLookupError:
            return ""
        except Exception as exc:
            return str(exc)

        deadline = time.time() + 8.0
        while time.time() < deadline:
            if not self._is_process_alive(pid):
                return ""
            time.sleep(0.1)

        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            return ""
        except Exception as exc:
            return str(exc)

        deadline = time.time() + 5.0
        while time.time() < deadline:
            if not self._is_process_alive(pid):
                return ""
            time.sleep(0.1)
        return f"Process group {pid} did not exit after SIGKILL"

    def _sync_orphaned_jobs(self) -> None:
        with self._lock:
            changed = self._reconcile_orphaned_jobs_locked()
            if changed:
                self._persist_state_locked()

    def _reconcile_orphaned_jobs_locked(self) -> bool:
        changed = False
        now = datetime.now().isoformat(timespec="seconds")
        for record in self._jobs.values():
            if record.status != "running":
                continue
            if record.job_id in self._procs:
                continue
            if self._is_process_alive(record.pid):
                continue
            record.status = "lost"
            if not record.ended_at:
                record.ended_at = now
            record.artifacts = self._discover_artifacts(record)
            changed = True
        return changed

    def _restore_state(self) -> None:
        restored = self._load_state_records()
        if not restored:
            restored = self._restore_from_logs()
        if not restored:
            return
        with self._lock:
            for record in restored:
                record.metadata.setdefault("restored", True)
                self._jobs[record.job_id] = record
            self._reconcile_orphaned_jobs_locked()
            self._enforce_history_limit_locked()
            self._persist_state_locked()

    def _load_state_records(self) -> list[JobRecord]:
        if not self._state_path.exists():
            return []
        try:
            raw = self._state_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(payload, list):
            return []

        records: list[JobRecord] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                records.append(JobRecord.from_dict(item))
            except ValueError:
                continue
        return sorted(records, key=lambda item: item.started_at, reverse=True)

    def _restore_from_logs(self) -> list[JobRecord]:
        if not self._logs_dir.exists():
            return []

        try:
            candidates = [path for path in self._logs_dir.glob("*.log") if path.is_file()]
        except OSError:
            return []

        candidates = sorted(
            candidates,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[: self._history_limit]

        restored: list[JobRecord] = []
        for log_path in candidates:
            record = self._restore_record_from_log(log_path)
            if record is not None:
                restored.append(record)
        return sorted(restored, key=lambda item: item.started_at, reverse=True)

    def _restore_record_from_log(self, log_path: Path) -> JobRecord | None:
        match = _JOB_LOG_RE.match(log_path.name)
        if not match:
            return None

        kind = match.group("kind")
        started_at = _stamp_to_iso(match.group("stamp"))
        display_command = ""
        pid: int | None = None

        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as fh:
                for _ in range(20):
                    line = fh.readline()
                    if not line:
                        break
                    text = line.strip()
                    if text.startswith("[web-gui] kind="):
                        kind = text.split("=", 1)[1].strip() or kind
                    elif text.startswith("[web-gui] started_at="):
                        started_at = text.split("=", 1)[1].strip() or started_at
                    elif text.startswith("[web-gui] command="):
                        display_command = text.split("=", 1)[1].strip()
                    elif text.startswith("[web-gui] pid="):
                        pid = _to_optional_int(text.split("=", 1)[1].strip())
        except OSError:
            return None

        status = "running" if self._is_process_alive(pid) else "restored"
        return JobRecord(
            job_id=match.group("job_id"),
            kind=kind,
            status=status,
            created_at=started_at,
            started_at=started_at,
            shell_command=display_command,
            display_command=display_command,
            log_path=str(log_path),
            pid=pid,
            metadata={"restored": True},
        )

    def _enforce_history_limit_locked(self) -> None:
        if len(self._jobs) <= self._history_limit:
            return

        rows = sorted(self._jobs.values(), key=lambda item: item.started_at, reverse=True)
        keep_ids = {item.job_id for item in rows if item.status == "running"}
        for item in rows:
            if len(keep_ids) >= self._history_limit:
                break
            keep_ids.add(item.job_id)

        self._jobs = {item.job_id: item for item in rows if item.job_id in keep_ids}
        self._procs = {job_id: proc for job_id, proc in self._procs.items() if job_id in keep_ids}

    def _persist_state_locked(self) -> None:
        rows = sorted(self._jobs.values(), key=lambda item: item.started_at, reverse=True)
        payload = [item.to_dict() for item in rows]
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._state_path.with_suffix(f"{self._state_path.suffix}.tmp")
            tmp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            tmp_path.replace(self._state_path)
        except OSError:
            return
