from __future__ import annotations

import os
from pathlib import Path


def test_with_colcon_lock_script_is_executable() -> None:
    path = Path("scripts/with_colcon_lock.sh")
    assert path.exists()
    assert os.access(path, os.X_OK)


def test_makefile_uses_colcon_lock_wrapper() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")
    assert "with_colcon_lock.sh colcon build" in content
    assert "with_colcon_lock.sh colcon test --base-paths ros2_ws/src" in content
    assert "with_colcon_lock.sh colcon test-result --verbose" in content


def test_runtime_scripts_use_colcon_lock_wrapper() -> None:
    files = [
        "scripts/run_demo.sh",
        "scripts/run_benchmarks.sh",
        "scripts/open_live_test_terminals.sh",
    ]
    for rel_path in files:
        content = Path(rel_path).read_text(encoding="utf-8")
        assert 'with_colcon_lock.sh" colcon build' in content
