from __future__ import annotations

from pathlib import Path

import pytest
from asr_gateway.log_views import collect_logs, detect_severity, log_files


def test_collect_logs_filters_requested_severity(tmp_path: Path) -> None:
    logs_root = tmp_path / "logs"
    runtime_dir = logs_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime.log").write_text(
        "INFO runtime started\nWARNING sample warning\nERROR sample error\n",
        encoding="utf-8",
    )

    rows = collect_logs(logs_root, "runtime", "error", 20)

    assert len(rows) == 1
    assert rows[0]["severity"] == "error"
    assert "sample error" in rows[0]["message"]


def test_log_files_returns_most_recent_known_component_files(tmp_path: Path) -> None:
    logs_root = tmp_path / "logs"
    gateway_dir = logs_root / "gateway"
    gateway_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(5):
        (gateway_dir / f"log_{idx}.log").write_text(f"INFO {idx}\n", encoding="utf-8")

    files = log_files(logs_root, "gateway")

    assert len(files) == 3
    assert all(path.parent == gateway_dir for path in files)


def test_detect_severity_defaults_to_info() -> None:
    assert detect_severity("plain informational line") == "info"


def test_detect_severity_treats_empty_json_error_field_as_info() -> None:
    assert detect_severity('    "error": ""') == "info"


def test_runtime_log_files_include_ros_log_dir_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs_root = tmp_path / "logs"
    runtime_dir = logs_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    ros_log_dir = tmp_path / "ros_logs"
    ros_log_dir.mkdir(parents=True, exist_ok=True)
    (ros_log_dir / "audio_input_node.log").write_text(
        "INFO runtime via ros log dir\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROS_LOG_DIR", str(ros_log_dir))

    files = log_files(logs_root, "runtime")

    assert any(path.parent == ros_log_dir for path in files)


def test_collect_logs_keeps_runtime_component_for_ros_fallback_and_sorts_newest_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs_root = tmp_path / "logs"
    runtime_dir = logs_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime.log").write_text(
        "2026-03-30T10:00:00Z INFO local runtime\n",
        encoding="utf-8",
    )

    ros_log_dir = tmp_path / "ros_logs"
    ros_log_dir.mkdir(parents=True, exist_ok=True)
    (ros_log_dir / "audio_input_node.log").write_text(
        "2026-03-30T10:00:01Z ERROR ros runtime failed\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROS_LOG_DIR", str(ros_log_dir))

    rows = collect_logs(logs_root, "runtime", "all", 20)

    assert rows[0]["component"] == "runtime"
    assert rows[0]["source"] == "audio_input_node.log"
    assert rows[0]["line_number"] == 1
    assert rows[0]["timestamp"] == "2026-03-30T10:00:01+00:00"
    assert "ros runtime failed" in rows[0]["message"]


def test_collect_logs_prefers_current_ros_session_over_stale_local_runtime_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs_root = tmp_path / "logs"
    stale_runtime_session = logs_root / "runtime" / "ros" / "2026-03-30-15-17-12-stale"
    stale_runtime_session.mkdir(parents=True, exist_ok=True)
    (stale_runtime_session / "launch.log").write_text(
        "2026-03-30T15:17:24Z ERROR stale benchmark_manager_node died\n",
        encoding="utf-8",
    )

    current_ros_session = tmp_path / "ros_logs" / "latest"
    current_ros_session.mkdir(parents=True, exist_ok=True)
    (current_ros_session / "launch.log").write_text(
        "2026-03-30T15:42:20Z INFO current benchmark_manager_node healthy\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROS_LOG_DIR", str(tmp_path / "ros_logs"))

    rows = collect_logs(logs_root, "runtime", "all", 20)

    assert rows[0]["source"] == "launch.log"
    assert "current benchmark_manager_node healthy" in rows[0]["message"]
    assert all("stale benchmark_manager_node died" not in row["message"] for row in rows)


def test_collect_logs_ignores_gui_state_json_files(
    tmp_path: Path,
) -> None:
    logs_root = tmp_path / "logs"
    gui_dir = logs_root / "gui" / "legacy_web_gui"
    gui_dir.mkdir(parents=True, exist_ok=True)
    (gui_dir / "jobs_state.json").write_text('[{"error": ""}]\n', encoding="utf-8")
    (gui_dir / "session.log").write_text("ERROR gui actual failure\n", encoding="utf-8")

    files = log_files(logs_root, "gui")
    rows = collect_logs(logs_root, "gui", "all", 20)

    assert files == [gui_dir / "session.log"]
    assert len(rows) == 1
    assert rows[0]["source"].endswith("session.log")
    assert rows[0]["severity"] == "error"
