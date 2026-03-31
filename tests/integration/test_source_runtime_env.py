from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def test_source_runtime_env_exports_project_runtime_log_dir(repo_root: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("ROS_LOG_DIR", None)
    env.pop("ASR_RUNTIME_LOG_DIR", None)
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f'cd "{repo_root}" && '
                'source scripts/source_runtime_env.sh --without-ros && '
                'printf "%s\\n%s\\n%s\\n" "$ASR_RUNTIME_LOG_DIR" "$ROS_LOG_DIR" "$ASR_COLCON_INSTALL_PREFIX"'
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    runtime_log_dir, ros_log_dir, install_prefix = result.stdout.strip().splitlines()[-3:]
    assert runtime_log_dir == str(repo_root / "logs" / "runtime")
    assert ros_log_dir == str(repo_root / "logs" / "runtime" / "ros")
    assert install_prefix == str(repo_root / "ros2_ws" / "install")
    assert (repo_root / "logs" / "runtime").is_dir()


def test_source_runtime_env_without_ros_excludes_legacy_python_packages_by_default(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env.pop("PYTHONPATH", None)
    (tmp_path / "home").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f'cd "{repo_root}" && '
                'source scripts/source_runtime_env.sh --without-ros && '
                'printf "%s\\n" "${PYTHONPATH:-}"'
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    pythonpath = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    entries = set(filter(None, pythonpath.split(os.pathsep)))
    assert str(repo_root / "ros2_ws" / "src" / "asr_ros") not in entries
    assert str(repo_root / "ros2_ws" / "src" / "asr_benchmark") not in entries


def test_source_runtime_env_without_ros_can_opt_in_legacy_python_packages(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["ASR_INCLUDE_LEGACY_PYTHONPATH"] = "1"
    env.pop("PYTHONPATH", None)
    (tmp_path / "home").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f'cd "{repo_root}" && '
                'source scripts/source_runtime_env.sh --without-ros && '
                'printf "%s\\n" "${PYTHONPATH:-}"'
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    pythonpath = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    entries = set(filter(None, pythonpath.split(os.pathsep)))
    assert str(repo_root / "ros2_ws" / "src" / "asr_ros") in entries
    assert str(repo_root / "ros2_ws" / "src" / "asr_benchmark") in entries


def test_run_rqt_check_env_reports_workspace_interfaces(repo_root: Path, tmp_path: Path) -> None:
    if not Path("/opt/ros/jazzy/setup.bash").exists():
        pytest.skip("ROS2 Jazzy is not installed")
    if not (repo_root / "ros2_ws" / "install" / "setup.bash").exists():
        pytest.skip("colcon workspace is not built")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'cd "{repo_root}" && bash scripts/run_rqt.sh --check-env',
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "rqt environment ready" in result.stdout


def test_source_runtime_env_with_ros_does_not_prepend_source_tree_to_pythonpath(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    if not Path("/opt/ros/jazzy/setup.bash").exists():
        pytest.skip("ROS2 Jazzy is not installed")
    if not (repo_root / "ros2_ws" / "install" / "setup.bash").exists():
        pytest.skip("colcon workspace is not built")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env.pop("PYTHONPATH", None)
    (tmp_path / "home").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f'cd "{repo_root}" && '
                'source scripts/source_runtime_env.sh --with-ros && '
                'printf "%s\\n" "${PYTHONPATH:-}"'
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    pythonpath = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    assert str(repo_root / "ros2_ws" / "src") not in pythonpath
