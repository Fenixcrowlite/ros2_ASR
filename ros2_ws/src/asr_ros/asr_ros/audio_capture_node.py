"""ROS2 audio producer node.

Publishes raw PCM chunks to `/asr/audio_chunks` either from microphone
or from WAV file input.
"""

from __future__ import annotations

import queue
import time
import wave
from pathlib import Path
from typing import Any

import rclpy
from asr_core.ros_parameters import (
    parameter_bool,
    parameter_float,
    parameter_int,
    parameter_string,
)
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray

from asr_ros.shutdown import safe_shutdown_node


def _coerce_int_param(
    raw: Any,
    *,
    name: str,
    default: int,
    min_value: int,
    logger: Any,
) -> int:
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid parameter '{name}={raw}', expected integer >= {min_value}. "
            f"Using default {default}."
        )
        return default
    if value < min_value:
        logger.warning(
            f"Out-of-range parameter '{name}={value}', expected >= {min_value}. "
            f"Using default {default}."
        )
        return default
    return value


def _coerce_float_param(
    raw: Any,
    *,
    name: str,
    default: float,
    min_value: float,
    logger: Any,
) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid parameter '{name}={raw}', expected float >= {min_value}. "
            f"Using default {default}."
        )
        return default
    if value < min_value:
        logger.warning(
            f"Out-of-range parameter '{name}={value}', expected >= {min_value}. "
            f"Using default {default}."
        )
        return default
    return value


def _next_power_of_two(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (int(value) - 1).bit_length()


def _mic_block_frames(sample_rate: int, chunk_ms: int) -> int:
    requested_frames = max(1, int(sample_rate * chunk_ms / 1000.0))
    return _next_power_of_two(requested_frames)


class AudioCaptureNode(Node):
    """Publish legacy raw audio chunks from a WAV file or microphone.

    Published topics:
    - `/asr/audio_chunks` (`std_msgs/UInt8MultiArray`)

    Subscribed topics:
    - none

    Parameters:
    - `input_mode`, `wav_path`, `device`
    - `sample_rate`, `chunk_ms`
    - `continuous`, `mic_capture_sec`
    """

    def __init__(self) -> None:
        super().__init__("audio_capture_node")
        numeric_descriptor = ParameterDescriptor(dynamic_typing=True)
        # Input parameters are intentionally simple for launch/YAML usage.
        self.declare_parameter("input_mode", "file")
        self.declare_parameter("wav_path", "data/sample/vosk_test.wav")
        self.declare_parameter("sample_rate", 16000, descriptor=numeric_descriptor)
        self.declare_parameter("chunk_ms", 800, descriptor=numeric_descriptor)
        self.declare_parameter("device", "")
        self.declare_parameter("continuous", True)
        self.declare_parameter("mic_capture_sec", 4.0, descriptor=numeric_descriptor)

        self.publisher = self.create_publisher(UInt8MultiArray, "/asr/audio_chunks", 10)
        self.input_mode = parameter_string(self, "input_mode")
        self.wav_path = parameter_string(self, "wav_path")
        self.sample_rate = _coerce_int_param(
            parameter_int(self, "sample_rate"),
            name="sample_rate",
            default=16000,
            min_value=8000,
            logger=self.get_logger(),
        )
        self.chunk_ms = _coerce_int_param(
            parameter_int(self, "chunk_ms"),
            name="chunk_ms",
            default=800,
            min_value=1,
            logger=self.get_logger(),
        )
        self.device = parameter_string(self, "device")
        self.continuous = parameter_bool(self, "continuous", default=True)
        self.mic_capture_sec = _coerce_float_param(
            parameter_float(self, "mic_capture_sec"),
            name="mic_capture_sec",
            default=4.0,
            min_value=0.1,
            logger=self.get_logger(),
        )

        self._timer = self.create_timer(1.0, self._on_timer)
        self._published_once = False
        self.get_logger().info(
            f"Audio capture initialized with mode={self.input_mode}, "
            f"continuous={self.continuous}, mic_capture_sec={self.mic_capture_sec}"
        )

    def _on_timer(self) -> None:
        """Run selected input mode on timer.

        In mic mode with `continuous=true` the node re-captures periodically.
        """
        if self._published_once:
            return
        mode = self.input_mode
        if mode == "mic":
            if self._publish_from_mic():
                if not self.continuous:
                    self._published_once = True
                return
            self.get_logger().error("Microphone capture failed; no fallback mode is applied")
            self._published_once = True
            return
        if mode not in {"file", "mic"}:
            self.get_logger().error(f"Unsupported input_mode: {mode}")
            self._published_once = True
            return
        if mode == "file":
            self._publish_from_file()
            self._published_once = True

    def _publish_from_file(self) -> None:
        """Publish pre-recorded WAV as PCM chunks."""
        wav = Path(self.wav_path)
        if not wav.exists():
            self.get_logger().error(f"WAV not found: {wav}")
            return
        with wave.open(str(wav), "rb") as wf:
            frames_per_chunk = int(wf.getframerate() * self.chunk_ms / 1000.0)
            while True:
                data = wf.readframes(frames_per_chunk)
                if not data:
                    break
                msg = UInt8MultiArray()
                msg.data = list(data)
                self.publisher.publish(msg)
        self.get_logger().info(f"Published file audio chunks from {wav}")

    def _publish_from_mic(self) -> bool:
        """Capture short microphone window and publish PCM chunks.

        Returns:
            `True` when microphone stream was opened and processed.
            `False` when microphone capture failed.
        """
        try:
            import sounddevice as sd
        except Exception as exc:
            self.get_logger().warning(
                f"sounddevice import failed; microphone capture disabled: {exc}"
            )
            return False

        audio_q: queue.Queue[bytes] = queue.Queue(maxsize=8)

        def callback(indata, frames, _time, status) -> None:
            """Sounddevice callback storing chunk bytes into queue."""
            if status:
                return
            payload = bytes(indata)
            try:
                audio_q.put_nowait(payload)
            except queue.Full:
                try:
                    audio_q.get_nowait()
                except queue.Empty:
                    pass
                audio_q.put_nowait(payload)

        try:
            chunk_frames = _mic_block_frames(self.sample_rate, self.chunk_ms)
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=chunk_frames,
                channels=1,
                dtype="int16",
                callback=callback,
                device=self.device if self.device else None,
            ):
                start = time.time()
                while time.time() - start < self.mic_capture_sec:
                    try:
                        payload = audio_q.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    msg = UInt8MultiArray()
                    msg.data = list(payload)
                    self.publisher.publish(msg)
            self.get_logger().info("Published microphone audio chunks")
            return True
        except Exception as exc:
            self.get_logger().error(f"Microphone capture failed: {exc}")
            return False


def main() -> None:
    rclpy.init()
    node = AudioCaptureNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
