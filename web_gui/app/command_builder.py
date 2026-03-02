"""Shell command builders for Web GUI actions."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from web_gui.app.paths import REPO_ROOT, RESULTS_ROOT


@dataclass(slots=True)
class CommandSpec:
    """Prepared shell command with metadata."""

    shell_command: str
    display_command: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _quoted_cmd(parts: list[str]) -> str:
    return " ".join(shlex.quote(item) for item in parts)


def _shell_preamble(*, include_ros: bool) -> str:
    base = [
        "set -euo pipefail",
        f"cd {shlex.quote(str(REPO_ROOT))}",
        "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi",
        (
            "export PYTHONPATH=\"${PYTHONPATH:-}:"
            f"$(find {shlex.quote(str(REPO_ROOT / 'ros2_ws' / 'src'))} "
            "-mindepth 1 -maxdepth 1 -type d | tr '\\n' ':')\""
        ),
    ]
    if include_ros:
        base.append(
            "if [ -f /opt/ros/jazzy/setup.bash ]; then "
            "set +u; source /opt/ros/jazzy/setup.bash; "
            "[ -f install/setup.bash ] && source install/setup.bash || true; "
            "set -u; "
            "else echo '[web-gui] WARN: /opt/ros/jazzy/setup.bash not found'; fi"
        )
    return " ; ".join(base)


def build_live_sample_command(runtime_config: Path, payload: dict[str, Any]) -> CommandSpec:
    """Build live-sample evaluator command."""
    args = [
        "python3",
        "scripts/live_sample_eval.py",
        "--config",
        str(runtime_config),
        "--interfaces",
        str(payload.get("interfaces") or "core"),
        "--model-runs",
        str(payload.get("model_runs") or payload.get("backends") or "mock"),
        "--language-mode",
        str(payload.get("language_mode") or "config"),
        "--record-sec",
        str(payload.get("record_sec") or 5.0),
        "--sample-rate",
        str(payload.get("sample_rate") or 16000),
        "--output-dir",
        str(payload.get("output_dir") or (RESULTS_ROOT / "live_sample")),
        "--sample-name",
        str(payload.get("sample_name") or "live_sample"),
        "--action-chunk-sec",
        str(payload.get("action_chunk_sec") or 0.8),
        "--request-timeout-sec",
        str(payload.get("request_timeout_sec") or 25.0),
    ]

    if payload.get("language"):
        args += ["--language", str(payload["language"])]
    if payload.get("reference_text"):
        args += ["--reference-text", str(payload["reference_text"])]
    if payload.get("device"):
        args += ["--device", str(payload["device"])]
    if payload.get("use_wav"):
        args += ["--use-wav", str(payload["use_wav"])]
    if bool(payload.get("ros_auto_launch", False)):
        args.append("--ros-auto-launch")
    if bool(payload.get("action_streaming", False)):
        args.append("--action-streaming")

    core_cmd = _quoted_cmd(args)
    shell = f"{_shell_preamble(include_ros=True)} ; {core_cmd}"
    return CommandSpec(
        shell_command=shell,
        display_command=core_cmd,
        metadata={
            "output_dir": str(payload.get("output_dir") or (RESULTS_ROOT / "live_sample")),
            "runtime_config": str(runtime_config),
        },
    )


def build_benchmark_command(runtime_config: Path, payload: dict[str, Any]) -> CommandSpec:
    """Build benchmark runner command."""
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(payload.get("output_dir") or (RESULTS_ROOT / "benchmark" / run_ts))
    output_json = run_dir / "benchmark_results.json"
    output_csv = run_dir / "benchmark_results.csv"
    report_md = run_dir / "report.md"

    args = [
        "python3",
        "-m",
        "asr_benchmark.runner",
        "--config",
        str(runtime_config),
        "--dataset",
        str(payload.get("dataset") or "data/transcripts/sample_manifest.csv"),
        "--output-json",
        str(output_json),
        "--output-csv",
        str(output_csv),
    ]

    backends = str(payload.get("backends") or "").strip()
    if backends:
        args += ["--backends", backends]

    runner_cmd = _quoted_cmd(args)
    report_cmd = _quoted_cmd(
        [
            "python3",
            "scripts/generate_report.py",
            "--input",
            str(output_json),
            "--output",
            str(report_md),
        ]
    )
    shell = (
        f"{_shell_preamble(include_ros=False)} ; "
        f"mkdir -p {shlex.quote(str(run_dir))} ; "
        f"{runner_cmd} ; "
        f"{report_cmd}"
    )
    return CommandSpec(
        shell_command=shell,
        display_command=f"{runner_cmd} && {report_cmd}",
        metadata={
            "run_dir": str(run_dir),
            "output_json": str(output_json),
            "output_csv": str(output_csv),
            "report": str(report_md),
            "runtime_config": str(runtime_config),
        },
    )


def build_ros_bringup_command(runtime_config: Path, payload: dict[str, Any]) -> CommandSpec:
    """Build long-running ROS2 bringup command."""
    args = [
        "ros2",
        "launch",
        "asr_ros",
        "bringup.launch.py",
        f"config:={runtime_config}",
        f"input_mode:={payload.get('input_mode') or 'mic'}",
        f"continuous:={str(payload.get('continuous', True)).lower()}",
        f"sample_rate:={payload.get('sample_rate') or 16000}",
        f"chunk_ms:={payload.get('chunk_ms') or 800}",
        f"mic_capture_sec:={payload.get('mic_capture_sec') or 4.0}",
        f"live_stream_enabled:={str(payload.get('live_stream_enabled', True)).lower()}",
        f"text_output_enabled:={str(payload.get('text_output_enabled', True)).lower()}",
    ]

    if payload.get("wav_path"):
        args.append(f"wav_path:={payload['wav_path']}")
    if payload.get("device"):
        args.append(f"device:={payload['device']}")

    ros_cmd = _quoted_cmd(args)
    shell = f"{_shell_preamble(include_ros=True)} ; {ros_cmd}"
    return CommandSpec(
        shell_command=shell,
        display_command=ros_cmd,
        metadata={"runtime_config": str(runtime_config)},
    )
