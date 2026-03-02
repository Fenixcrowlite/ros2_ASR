from __future__ import annotations

from pathlib import Path

from web_gui.app.command_builder import (
    build_benchmark_command,
    build_live_sample_command,
    build_ros_bringup_command,
)


def test_build_live_sample_command_contains_essential_flags() -> None:
    cmd = build_live_sample_command(
        Path("configs/default.yaml"),
        {
            "interfaces": "core,ros_service",
            "model_runs": "whisper:tiny,mock",
            "language_mode": "auto",
            "record_sec": 3,
            "sample_rate": 16000,
            "ros_auto_launch": True,
        },
    )
    assert "scripts/live_sample_eval.py" in cmd.display_command
    assert "--model-runs" in cmd.display_command
    assert "--ros-auto-launch" in cmd.display_command
    assert "--language-mode" in cmd.display_command


def test_build_benchmark_command_outputs_metadata_paths() -> None:
    cmd = build_benchmark_command(
        Path("configs/default.yaml"),
        {"dataset": "data/transcripts/sample_manifest.csv", "backends": "mock,whisper"},
    )
    assert "asr_benchmark.runner" in cmd.display_command
    assert cmd.metadata["output_json"].endswith("benchmark_results.json")
    assert cmd.metadata["report"].endswith("report.md")


def test_build_ros_bringup_command_contains_launch_args() -> None:
    cmd = build_ros_bringup_command(
        Path("configs/default.yaml"),
        {
            "input_mode": "mic",
            "continuous": True,
            "text_output_enabled": True,
            "sample_rate": 16000,
        },
    )
    assert "ros2" in cmd.display_command
    assert "bringup.launch.py" in cmd.display_command
    assert "text_output_enabled:=true" in cmd.display_command
