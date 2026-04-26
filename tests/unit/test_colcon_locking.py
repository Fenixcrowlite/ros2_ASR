from __future__ import annotations

import os
import re
from pathlib import Path


def test_with_colcon_lock_script_is_executable() -> None:
    path = Path("scripts/with_colcon_lock.sh")
    assert path.exists()
    assert os.access(path, os.X_OK)


def test_makefile_uses_colcon_lock_wrapper() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")
    assert re.search(r"with_colcon_lock\.sh colcon [^\n]*\bbuild\b", content)
    assert re.search(r"with_colcon_lock\.sh colcon [^\n]*\btest\b", content)
    assert re.search(r"with_colcon_lock\.sh colcon [^\n]*\btest-result\b", content)
    assert not re.search(r"colcon [^\n]*\btest\b[^\n]*--symlink-install", content)


def test_runtime_scripts_use_colcon_lock_wrapper() -> None:
    files = [
        "scripts/run_demo.sh",
        "scripts/run_benchmarks.sh",
        "scripts/open_live_test_terminals.sh",
    ]
    for rel_path in files:
        content = Path(rel_path).read_text(encoding="utf-8")
        assert re.search(r'with_colcon_lock\.sh" colcon [^\n]*\bbuild\b', content)


def test_runtime_scripts_target_current_launch_stack() -> None:
    run_demo = Path("scripts/run_demo.sh").read_text(encoding="utf-8")
    open_live = Path("scripts/open_live_test_terminals.sh").read_text(encoding="utf-8")

    assert "ros2 launch asr_launch runtime_minimal.launch.py" in run_demo
    assert "--packages-skip asr_ros asr_benchmark" not in run_demo
    assert "ros2 launch asr_launch runtime_streaming.launch.py" in open_live
    assert "/asr/runtime/start_session" in open_live
    assert "/asr/runtime/results/final" in open_live
    assert "ros2 launch asr_ros" not in run_demo
    assert "asr_ros" not in open_live
    assert "mic, file, auto" not in open_live
    assert "INPUT_MODE must be one of: mic, file" in open_live


def test_release_check_covers_ros_and_colcon() -> None:
    content = Path("scripts/release_check.sh").read_text(encoding="utf-8")
    assert "make test-ros" in content
    assert "make test-colcon" in content
