"""ROS2 audio producer node.

Publishes raw PCM chunks to `/asr/audio_chunks` either from microphone
or from WAV file fallback mode.
"""

from __future__ import annotations

import queue
import time
import wave
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray


class AudioCaptureNode(Node):
    """Capture audio and publish chunked payload for ASR server."""

    def __init__(self) -> None:
        super().__init__("audio_capture_node")
        # Input parameters are intentionally simple for launch/YAML usage.
        self.declare_parameter("input_mode", "auto")
        self.declare_parameter("wav_path", "data/sample/en_hello.wav")
        self.declare_parameter("sample_rate", 16000)
        self.declare_parameter("chunk_ms", 800)
        self.declare_parameter("device", "")
        self.declare_parameter("continuous", True)
        self.declare_parameter("mic_capture_sec", 4.0)

        self.publisher = self.create_publisher(UInt8MultiArray, "/asr/audio_chunks", 10)
        self.input_mode = str(self.get_parameter("input_mode").value)
        self.wav_path = str(self.get_parameter("wav_path").value)
        self.sample_rate = int(self.get_parameter("sample_rate").value)
        self.chunk_ms = int(self.get_parameter("chunk_ms").value)
        self.device = str(self.get_parameter("device").value)
        continuous_raw = self.get_parameter("continuous").value
        if isinstance(continuous_raw, str):
            self.continuous = continuous_raw.lower() in {"1", "true", "yes", "on"}
        else:
            self.continuous = bool(continuous_raw)
        self.mic_capture_sec = float(self.get_parameter("mic_capture_sec").value)

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
        if mode == "auto":
            mode = "mic"
        if mode == "mic":
            if self._publish_from_mic():
                if not self.continuous:
                    self._published_once = True
                return
            self.get_logger().warning("Microphone unavailable, falling back to file mode")
            self.input_mode = "file"
            mode = "file"
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
            `False` when microphone is unavailable (caller should fallback).
        """
        try:
            import sounddevice as sd
        except Exception:
            return False

        audio_q: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, _time, status) -> None:
            """Sounddevice callback storing chunk bytes into queue."""
            if status:
                return
            audio_q.put(bytes(indata))

        try:
            chunk_frames = int(self.sample_rate * self.chunk_ms / 1000.0)
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
        except Exception:
            return False


def main() -> None:
    rclpy.init()
    node = AudioCaptureNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
