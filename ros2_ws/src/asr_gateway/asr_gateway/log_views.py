"""Helpers for log discovery and filtering views."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def tail_lines(path: Path, limit: int) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    return content[-limit:]


def detect_severity(line: str) -> str:
    lowered = line.lower()
    if "error" in lowered:
        return "error"
    if "warn" in lowered:
        return "warning"
    if "debug" in lowered:
        return "debug"
    return "info"


def _runtime_log_bases(logs_root: Path) -> list[Path]:
    bases = [logs_root / "runtime"]
    env_ros_log_dir = str(os.getenv("ROS_LOG_DIR", "")).strip()
    if env_ros_log_dir:
        bases.append(Path(env_ros_log_dir).expanduser())

    default_ros_log_dir = Path.home() / ".ros" / "log"
    if default_ros_log_dir.exists():
        latest = default_ros_log_dir / "latest"
        if latest.exists():
            bases.append(latest)
        bases.append(default_ros_log_dir)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for base in bases:
        resolved = base.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(base)
    return deduped


def _base_has_log_files(base: Path) -> bool:
    return any(path.is_file() and path.name != ".gitkeep" for path in base.rglob("*"))


def log_files(logs_root: Path, component: str) -> list[Path]:
    runtime_root = logs_root / "runtime"
    runtime_bases = [runtime_root] if runtime_root.exists() and _base_has_log_files(runtime_root) else _runtime_log_bases(logs_root)
    mapping = {
        "runtime": runtime_bases,
        "benchmark": [logs_root / "benchmark"],
        "gateway": [logs_root / "gateway"],
        "gui": [logs_root / "gui"],
    }
    components = [component] if component != "all" else sorted(mapping.keys())

    files: list[Path] = []
    for comp in components:
        for base in mapping.get(comp, []):
            if not base.exists():
                continue
            candidates = [
                path
                for path in base.rglob("*")
                if path.is_file() and path.name != ".gitkeep"
            ]
            candidates.sort(key=_safe_mtime, reverse=True)
            files.extend(candidates[:3])
    files.sort(key=_safe_mtime, reverse=True)
    return files


def collect_logs(
    logs_root: Path,
    component: str,
    severity: str,
    limit: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    sev = severity.lower()
    for path in log_files(logs_root, component):
        try:
            rel = path.relative_to(logs_root)
            comp = rel.parts[0] if rel.parts else "unknown"
        except ValueError:
            comp = "unknown"
        for line in tail_lines(path, limit):
            detected = detect_severity(line)
            if sev != "all" and detected != sev:
                continue
            output.append(
                {
                    "component": comp,
                    "file": str(path),
                    "severity": detected,
                    "message": line,
                }
            )
    return output[-limit:]
