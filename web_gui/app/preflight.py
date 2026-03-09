"""Environment preflight checks for Web GUI runtime."""

from __future__ import annotations

import importlib.util
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from web_gui.app.paths import REPO_ROOT


def _module_ok(module_name: str) -> tuple[bool, str]:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return False, f"Module not installed: {module_name}"
    return True, "ok"


def _check_microphone_stack() -> tuple[bool, str, dict[str, Any]]:
    details: dict[str, Any] = {}
    try:
        import sounddevice as sd  # type: ignore
        import soundfile as sf  # type: ignore

        details["sounddevice"] = getattr(sd, "__version__", "unknown")
        details["soundfile"] = getattr(sf, "__version__", "unknown")
        try:
            devices = sd.query_devices()
            default_in, _default_out = sd.default.device
            details["audio_device_count"] = len(devices)
            details["default_input"] = int(default_in) if default_in is not None else None
        except Exception as exc:  # pragma: no cover - device availability can vary
            return False, f"Audio device query failed: {exc}", details
        return True, "ok", details
    except Exception as exc:
        return False, str(exc), details


def _resolve_entrypoint_python(entrypoint: Path) -> tuple[str | None, str]:
    if not entrypoint.exists():
        return None, f"Entrypoint not found: {entrypoint}"
    try:
        with entrypoint.open("r", encoding="utf-8", errors="replace") as fh:
            first_line = fh.readline().strip()
    except Exception as exc:
        return None, f"Unable to read entrypoint: {exc}"

    if not first_line.startswith("#!"):
        return None, f"Entrypoint has no shebang: {entrypoint}"

    shebang = first_line[2:].strip()
    if not shebang:
        return None, f"Entrypoint shebang is empty: {entrypoint}"

    parts = shlex.split(shebang)
    if not parts:
        return None, f"Entrypoint shebang is invalid: {entrypoint}"

    if Path(parts[0]).name == "env":
        if len(parts) < 2:
            return None, f"Entrypoint env shebang is invalid: {entrypoint}"
        resolved = shutil.which(parts[1]) or parts[1]
        return resolved, f"shebang={shebang}"
    return parts[0], f"shebang={shebang}"


def _module_ok_via_python(python_exec: str | None, module_name: str) -> tuple[bool, str]:
    if not python_exec:
        return False, "Python executable is not defined"

    check_code = (
        "import importlib.util, sys; "
        f"sys.exit(0 if importlib.util.find_spec({module_name!r}) else 2)"
    )
    try:
        result = subprocess.run(
            [python_exec, "-c", check_code],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except FileNotFoundError:
        return False, f"Python executable not found: {python_exec}"
    except Exception as exc:
        return False, f"Unable to run module check with {python_exec}: {exc}"

    if result.returncode == 0:
        return True, f"{python_exec} imports {module_name}"

    details = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
    return False, f"{python_exec} cannot import {module_name}: {details}"


def run_preflight_checks() -> dict[str, Any]:
    """Collect runtime readiness checks used by GUI and diagnostics."""
    required_modules = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "soundfile": "soundfile",
        "sounddevice": "sounddevice",
        "faster_whisper": "faster_whisper",
        "vosk": "vosk",
        "google_cloud_speech": "google.cloud.speech",
        "boto3": "boto3",
        "azure_speech": "azure.cognitiveservices.speech",
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "psutil": "psutil",
        "yaml": "yaml",
    }

    module_checks: dict[str, dict[str, Any]] = {}
    for label, module_name in required_modules.items():
        ok, message = _module_ok(module_name)
        module_checks[label] = {"ok": ok, "message": message}

    ros_setup = Path("/opt/ros/jazzy/setup.bash")
    install_setup = REPO_ROOT / "install" / "setup.bash"
    ros_executable = shutil.which("ros2")
    ros_available_via_setup = ros_setup.exists()
    text_node_exec = REPO_ROOT / "install" / "asr_ros" / "lib" / "asr_ros" / "asr_text_output_node"
    asr_server_exec = REPO_ROOT / "install" / "asr_ros" / "lib" / "asr_ros" / "asr_server_node"
    asr_server_python, asr_server_python_message = _resolve_entrypoint_python(asr_server_exec)
    asr_server_fw_ok, asr_server_fw_message = _module_ok_via_python(
        asr_server_python,
        "faster_whisper",
    )

    mic_ok, mic_message, mic_details = _check_microphone_stack()

    checks = {
        "modules": module_checks,
        "microphone": {
            "ok": mic_ok,
            "message": mic_message,
            "details": mic_details,
        },
        "ros": {
            "ros2_binary": {
                "ok": bool(ros_executable or ros_available_via_setup),
                "message": ros_executable
                or "ros2 not in current PATH, but /opt/ros/jazzy/setup.bash is available",
            },
            "jazzy_setup": {
                "ok": ros_setup.exists(),
                "message": str(ros_setup),
            },
            "install_setup": {
                "ok": install_setup.exists(),
                "message": str(install_setup),
            },
            "text_output_node_installed": {
                "ok": text_node_exec.exists(),
                "message": str(text_node_exec),
            },
            "asr_server_python": {
                "ok": bool(asr_server_python),
                "message": asr_server_python_message,
            },
            "asr_server_faster_whisper": {
                "ok": asr_server_fw_ok,
                "message": asr_server_fw_message,
            },
        },
    }

    ok = True
    for group in checks.values():
        if isinstance(group, dict):
            for item in group.values():
                if isinstance(item, dict) and "ok" in item and not bool(item["ok"]):
                    ok = False

    return {
        "ok": ok,
        "checks": checks,
    }
