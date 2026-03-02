"""Environment preflight checks for Web GUI runtime."""

from __future__ import annotations

import importlib.util
import shutil
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
