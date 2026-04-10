"""Helpers for log discovery and filtering views."""

from __future__ import annotations

import os
import re
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROS_TIME_RE = re.compile(r"\[([0-9]+(?:\.[0-9]+)?)\]")
ISO_TIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)"
)
EMPTY_JSON_ERROR_RE = re.compile(r'^\s*"error"\s*:\s*(""|null)\s*,?\s*$')
LOG_LIKE_SUFFIXES = {".log", ".txt", ".out", ".err"}


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def tail_lines(path: Path, limit: int) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        lines: deque[str] = deque(maxlen=max(limit, 1))
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                lines.append(line.rstrip("\n"))
    except OSError:
        return []
    return list(lines)


def _tail_rows(path: Path, limit: int) -> list[tuple[int, str]]:
    if not path.exists() or not path.is_file():
        return []
    try:
        rows: deque[tuple[int, str]] = deque(maxlen=max(limit, 1))
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                rows.append((line_number, line.rstrip("\n")))
    except OSError:
        return []
    return list(rows)


def detect_severity(line: str) -> str:
    if EMPTY_JSON_ERROR_RE.match(line.strip()):
        return "info"
    lowered = line.lower()
    if re.search(r"\berror\b", lowered):
        return "error"
    if re.search(r"\bwarn(?:ing)?\b", lowered):
        return "warning"
    if re.search(r"\bdebug\b", lowered):
        return "debug"
    return "info"


def _is_log_like_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in LOG_LIKE_SUFFIXES


def _runtime_log_bases(logs_root: Path) -> list[Path]:
    local_runtime_root = logs_root / "runtime"
    local_ros_log_dir = local_runtime_root / "ros"
    env_ros_log_dir = str(os.getenv("ROS_LOG_DIR", "")).strip()
    default_ros_log_dir = Path.home() / ".ros" / "log"

    preferred: list[Path] = []
    if env_ros_log_dir:
        latest_env_base = _latest_log_base(Path(env_ros_log_dir).expanduser())
        if latest_env_base is not None:
            preferred.append(latest_env_base)
    else:
        latest_default_base = _latest_log_base(default_ros_log_dir)
        if latest_default_base is not None:
            preferred.append(latest_default_base)

    latest_local_base = _latest_log_base(local_ros_log_dir)
    if latest_local_base is not None and not preferred:
        preferred.append(latest_local_base)
    elif latest_local_base is None and _base_has_log_files(local_runtime_root):
        preferred.append(local_runtime_root)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for base in preferred:
        resolved = base.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(base)
    return deduped


def _latest_log_base(base: Path) -> Path | None:
    if not base.exists():
        return None

    latest = base / "latest"
    if latest.exists() and latest.is_dir() and _base_has_log_files(latest):
        return latest

    try:
        subdirs = [path for path in base.iterdir() if path.is_dir() and path.name != "latest"]
    except OSError:
        subdirs = []
    subdirs.sort(key=_safe_mtime, reverse=True)
    for path in subdirs:
        if _base_has_log_files(path):
            return path

    if _base_has_log_files(base):
        return base
    return None


def _base_has_log_files(base: Path) -> bool:
    return any(path.is_file() and path.name != ".gitkeep" for path in base.rglob("*"))


def _component_bases(logs_root: Path, component: str) -> list[tuple[str, Path]]:
    runtime_bases = [
        base
        for base in _runtime_log_bases(logs_root)
        if base.exists() and _base_has_log_files(base)
    ]
    mapping = {
        "runtime": runtime_bases,
        "benchmark": [logs_root / "benchmark"],
        "gateway": [logs_root / "gateway"],
        "gui": [logs_root / "gui"],
    }
    components = [component] if component != "all" else sorted(mapping.keys())
    output: list[tuple[str, Path]] = []
    for comp in components:
        for base in mapping.get(comp, []):
            if not base.exists():
                continue
            output.append((comp, base))
    return output


def _component_files(logs_root: Path, component: str) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for comp, base in _component_bases(logs_root, component):
        candidates = [
            path
            for path in base.rglob("*")
            if path.is_file() and path.name != ".gitkeep" and _is_log_like_file(path)
        ]
        candidates.sort(key=_safe_mtime, reverse=True)
        for path in candidates[:3]:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append((comp, path))
    files.sort(key=lambda item: _safe_mtime(item[1]), reverse=True)
    return files


def log_files(logs_root: Path, component: str) -> list[Path]:
    return [path for _, path in _component_files(logs_root, component)]


def _parse_timestamp(line: str) -> str:
    ros_match = ROS_TIME_RE.search(line)
    if ros_match:
        raw = ros_match.group(1).strip()
        try:
            if "." in raw:
                value = float(raw)
                if 946684800.0 <= value <= 4102444800.0:
                    return datetime.fromtimestamp(value, tz=UTC).isoformat()
            elif 9 <= len(raw) <= 10:
                value = float(raw)
                if 946684800.0 <= value <= 4102444800.0:
                    return datetime.fromtimestamp(value, tz=UTC).isoformat()
        except ValueError:
            return ""
    iso_match = ISO_TIME_RE.search(line)
    if iso_match:
        raw = iso_match.group(1)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
        except ValueError:
            return raw
    return ""


def collect_logs(
    logs_root: Path,
    component: str,
    severity: str,
    limit: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    sev = severity.lower()
    for comp, path in _component_files(logs_root, component):
        file_mtime = _safe_mtime(path)
        display_name = path.name
        try:
            display_name = str(path.relative_to(logs_root))
        except ValueError:
            display_name = path.name
        for line_number, line in _tail_rows(path, limit):
            detected = detect_severity(line)
            if sev != "all" and detected != sev:
                continue
            parsed_timestamp = _parse_timestamp(line)
            sort_ts = file_mtime
            if parsed_timestamp:
                try:
                    sort_ts = datetime.fromisoformat(parsed_timestamp).timestamp()
                except ValueError:
                    sort_ts = file_mtime
            output.append(
                {
                    "component": comp,
                    "file": str(path),
                    "source": display_name,
                    "severity": detected,
                    "timestamp": parsed_timestamp,
                    "line_number": line_number,
                    "message": line,
                    "_sort_ts": sort_ts,
                }
            )
    output.sort(
        key=lambda item: (
            float(item.get("_sort_ts", 0.0) or 0.0),
            str(item.get("file", "")),
            int(item.get("line_number", 0) or 0),
        ),
        reverse=True,
    )
    trimmed = output[:limit]
    for item in trimmed:
        item.pop("_sort_ts", None)
    return trimmed
