"""Filesystem paths and helpers for Web GUI module."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_GUI_ROOT = REPO_ROOT / "web_gui"
RUNTIME_CONFIGS_DIR = WEB_GUI_ROOT / "runtime_configs"
UPLOADS_DIR = WEB_GUI_ROOT / "uploads"
NOISY_DIR = WEB_GUI_ROOT / "noisy"
PROFILES_DIR = WEB_GUI_ROOT / "profiles"
AWS_AUTH_PROFILES_DIR = WEB_GUI_ROOT / "auth_profiles"
RUNTIME_AWS_DIR = WEB_GUI_ROOT / "runtime_aws"
LOGS_DIR = WEB_GUI_ROOT / "logs"
RESULTS_ROOT = REPO_ROOT / "results" / "web_gui"


def ensure_directories() -> None:
    """Create working directories used by Web GUI if they do not exist."""
    for path in [
        WEB_GUI_ROOT,
        RUNTIME_CONFIGS_DIR,
        UPLOADS_DIR,
        NOISY_DIR,
        PROFILES_DIR,
        AWS_AUTH_PROFILES_DIR,
        RUNTIME_AWS_DIR,
        LOGS_DIR,
        RESULTS_ROOT,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def resolve_under_roots(raw_path: str, *, roots: list[Path]) -> Path:
    """Resolve path and enforce it is inside one of allowed roots."""
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    resolved = path.resolve()

    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return resolved
        except ValueError:
            continue
    allowed = ", ".join(str(item.resolve()) for item in roots)
    raise ValueError(f"Path '{resolved}' is outside allowed roots: {allowed}")
