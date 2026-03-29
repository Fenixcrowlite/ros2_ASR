"""Launch-time environment helpers for Python ROS nodes."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _prepend_unique(candidate: str, current: str) -> str:
    if not candidate:
        return current
    if not current:
        return candidate
    entries = current.split(os.pathsep)
    if candidate in entries:
        return current
    return os.pathsep.join([candidate, *entries])


def runtime_python_env() -> dict[str, str]:
    """Return env vars that let ROS Python entrypoints see active venv packages."""
    venv_root = Path(os.environ.get("VIRTUAL_ENV", "")).expanduser()
    if not venv_root:
        return {}

    py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = venv_root / "lib" / py_version / "site-packages"
    if not site_packages.is_dir():
        return {}

    env: dict[str, str] = {
        "PYTHONPATH": _prepend_unique(str(site_packages), os.environ.get("PYTHONPATH", "")),
    }

    ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    for lib_dir in sorted((site_packages / "nvidia").glob("*/lib")):
        if lib_dir.is_dir():
            ld_library_path = _prepend_unique(str(lib_dir), ld_library_path)
    if ld_library_path:
        env["LD_LIBRARY_PATH"] = ld_library_path

    return env
