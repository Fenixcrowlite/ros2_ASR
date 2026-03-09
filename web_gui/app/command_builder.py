"""Shell command builders for Web GUI actions."""

from __future__ import annotations

import math
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


def _float_literal(value: Any, default: float) -> str:
    """Return numeric literal with decimal point to keep ROS launch type DOUBLE."""
    raw = default if value in {None, ""} else value
    try:
        numeric = float(raw)
    except (TypeError, ValueError):
        numeric = float(default)
    if not math.isfinite(numeric):
        numeric = float(default)
    text = str(numeric)
    if "." in text or "e" in text.lower():
        return text
    return f"{text}.0"


def _int_literal(value: Any, default: int) -> str:
    """Return integer literal for CLI/launch args that expect INT values."""
    raw = default if value in {None, ""} else value
    try:
        numeric = float(raw)
        if not math.isfinite(numeric):
            raise ValueError("non-finite integer literal")
    except (TypeError, ValueError):
        numeric = float(default)
    return str(int(numeric))


def _shell_preamble(*, include_ros: bool) -> str:
    env_script = REPO_ROOT / "scripts" / "source_runtime_env.sh"
    env_mode = "--with-ros" if include_ros else "--without-ros"
    base = [
        "set -euo pipefail",
        f"cd {shlex.quote(str(REPO_ROOT))}",
        (
            f"if [ -f {shlex.quote(str(env_script))} ]; then "
            f"source {shlex.quote(str(env_script))} {env_mode}; "
            f"else echo '[web-gui] WARN: {env_script} not found'; fi"
        ),
    ]
    if include_ros:
        base.append("command -v ros2 >/dev/null || echo '[web-gui] WARN: ros2 is not in PATH'")
    return " ; ".join(base)


def build_live_sample_command(runtime_config: Path, payload: dict[str, Any]) -> CommandSpec:
    """Build live-sample evaluator command."""
    sample_rate_literal = _int_literal(payload.get("sample_rate"), 16000)
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
        sample_rate_literal,
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
    sample_rate_literal = _int_literal(payload.get("sample_rate"), 16000)
    chunk_ms_literal = _int_literal(payload.get("chunk_ms"), 800)
    mic_capture_sec_literal = _float_literal(payload.get("mic_capture_sec"), 4.0)
    args = [
        "ros2",
        "launch",
        "asr_ros",
        "bringup.launch.py",
        f"config:={runtime_config}",
        f"input_mode:={payload.get('input_mode') or 'mic'}",
        f"continuous:={str(payload.get('continuous', True)).lower()}",
        f"sample_rate:={sample_rate_literal}",
        f"chunk_ms:={chunk_ms_literal}",
        f"mic_capture_sec:={mic_capture_sec_literal}",
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
