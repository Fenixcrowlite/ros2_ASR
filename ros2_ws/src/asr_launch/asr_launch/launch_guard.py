"""Launch-time process guards for managed ASR stacks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_MANAGED_EXECUTABLES = (
    "audio_input_node",
    "audio_preprocess_node",
    "vad_segmenter_node",
    "asr_orchestrator_node",
    "benchmark_manager_node",
    "asr_gateway_server",
)


def _find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "ros2_ws" / "src").is_dir() and (candidate / "scripts").is_dir():
            return candidate
    return start.resolve()


def _managed_install_markers(project_root: Path) -> tuple[str, ...]:
    install_root = project_root / "ros2_ws" / "install"
    return tuple(str(install_root / package) for package in ("asr_runtime_nodes", "asr_gateway", "asr_benchmark_nodes"))


def detect_conflicting_managed_processes(
    ps_output: str,
    *,
    project_root: Path,
    exclude_pids: set[int] | None = None,
) -> list[dict[str, object]]:
    exclude = set(exclude_pids or set())
    markers = _managed_install_markers(project_root)
    conflicts: list[dict[str, object]] = []
    for raw_line in ps_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        pid_text, _, args = line.partition(" ")
        if not pid_text.isdigit() or not args:
            continue
        pid = int(pid_text)
        if pid in exclude:
            continue
        if not any(marker in args for marker in markers):
            continue
        if not any(executable in args for executable in _MANAGED_EXECUTABLES):
            continue
        conflicts.append({"pid": pid, "args": args})
    return conflicts


def assert_no_conflicting_managed_stack() -> None:
    project_root = _find_project_root(Path(__file__))
    ps_output = subprocess.run(
        ["ps", "-eo", "pid=,args="],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    conflicts = detect_conflicting_managed_processes(
        ps_output,
        project_root=project_root,
        exclude_pids={os.getpid(), os.getppid()},
    )
    if not conflicts:
        return
    details = "\n".join(f"  pid={item['pid']}: {item['args']}" for item in conflicts)
    raise RuntimeError(
        "Another managed ASR stack from this workspace is already running.\n"
        "Stop it before launching a new stack to avoid mixed ROS topics/services/logs.\n"
        f"{details}"
    )
