from __future__ import annotations

import sys
import types

import asr_ros.audio_capture_node as legacy_audio_capture_module
import pytest

if "rcl_interfaces.msg" not in sys.modules:
    rcl_interfaces_mod = types.ModuleType("rcl_interfaces")
    rcl_interfaces_msg_mod = types.ModuleType("rcl_interfaces.msg")

    class _ParameterDescriptor:
        def __init__(self, **kwargs) -> None:
            del kwargs

    rcl_interfaces_msg_mod.ParameterDescriptor = _ParameterDescriptor
    rcl_interfaces_mod.msg = rcl_interfaces_msg_mod
    sys.modules["rcl_interfaces"] = rcl_interfaces_mod
    sys.modules["rcl_interfaces.msg"] = rcl_interfaces_msg_mod

if "std_msgs.msg" not in sys.modules:
    std_msgs_mod = types.ModuleType("std_msgs")
    std_msgs_msg_mod = types.ModuleType("std_msgs.msg")

    class _UInt8MultiArray:
        def __init__(self) -> None:
            self.data = []

    std_msgs_msg_mod.UInt8MultiArray = _UInt8MultiArray
    std_msgs_mod.msg = std_msgs_msg_mod
    sys.modules["std_msgs"] = std_msgs_mod
    sys.modules["std_msgs.msg"] = std_msgs_msg_mod

if "rclpy.executors" in sys.modules and not hasattr(sys.modules["rclpy.executors"], "ExternalShutdownException"):
    class _ExternalShutdownException(Exception):
        pass

    sys.modules["rclpy.executors"].ExternalShutdownException = _ExternalShutdownException

from asr_ros.audio_capture_node import AudioCaptureNode

pytestmark = pytest.mark.legacy


class _FakeLogger:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)


class _FakeLegacyAudioCaptureNode:
    def __init__(self, *, input_mode: str, mic_success: bool) -> None:
        self.input_mode = input_mode
        self.continuous = False
        self._published_once = False
        self.logger = _FakeLogger()
        self.mic_attempts = 0
        self.file_attempts = 0
        self._mic_success = mic_success

    def get_logger(self):
        return self.logger

    def _publish_from_mic(self) -> bool:
        self.mic_attempts += 1
        return self._mic_success

    def _publish_from_file(self) -> None:
        self.file_attempts += 1


def test_legacy_audio_capture_rejects_mic_failure_without_file_fallback() -> None:
    node = _FakeLegacyAudioCaptureNode(input_mode="mic", mic_success=False)

    AudioCaptureNode._on_timer(node)

    assert node.mic_attempts == 1
    assert node.file_attempts == 0
    assert node._published_once is True
    assert node.logger.errors == ["Microphone capture failed; no fallback mode is applied"]


def test_legacy_audio_capture_rejects_unknown_mode() -> None:
    node = _FakeLegacyAudioCaptureNode(input_mode="auto", mic_success=False)

    AudioCaptureNode._on_timer(node)

    assert node.mic_attempts == 0
    assert node.file_attempts == 0
    assert node._published_once is True
    assert node.logger.errors == ["Unsupported input_mode: auto"]


def test_legacy_audio_capture_uses_power_of_two_mic_block_frames() -> None:
    assert legacy_audio_capture_module._mic_block_frames(16000, 800) == 16384
