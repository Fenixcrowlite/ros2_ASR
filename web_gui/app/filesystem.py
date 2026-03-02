"""File discovery helpers used by Web GUI API."""

from __future__ import annotations

from pathlib import Path

from web_gui.app.paths import NOISY_DIR, RESULTS_ROOT, UPLOADS_DIR


def _collect_files(root: Path, *, patterns: list[str]) -> list[str]:
    if not root.exists():
        return []
    results: list[str] = []
    for pattern in patterns:
        for item in root.glob(pattern):
            if item.is_file():
                results.append(str(item.resolve()))
    return sorted(set(results))


def list_uploads() -> list[str]:
    """List uploaded assets available for running experiments."""
    return _collect_files(
        UPLOADS_DIR,
        patterns=["*.wav", "*.csv", "*.yaml", "*.yml", "*.json", "*.txt"],
    )


def list_noisy_samples() -> list[str]:
    """List generated noisy WAV files."""
    return _collect_files(NOISY_DIR, patterns=["*.wav"])


def list_results() -> list[str]:
    """List generated result artifacts from Web GUI runs."""
    return _collect_files(
        RESULTS_ROOT,
        patterns=["**/*.json", "**/*.csv", "**/*.md", "**/*.png", "**/*.wav", "**/*.log"],
    )
