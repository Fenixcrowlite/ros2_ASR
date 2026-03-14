"""Audio input node publishing raw chunks from microphone or file."""

from __future__ import annotations

import queue
import threading
import time
import wave
from pathlib import Path

import rclpy
from asr_config import resolve_profile, validate_runtime_payload
from asr_core.ids import make_session_id
from asr_core.namespaces import TOPICS
from asr_core.shutdown import safe_shutdown_node
from asr_interfaces.msg import AudioChunk, NodeStatus
from asr_interfaces.srv import ReconfigureRuntime, StartRuntimeSession, StopRuntimeSession
from rclpy.node import Node


class AudioInputNode(Node):
    def __init__(self) -> None:
        super().__init__("audio_input_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("input_mode", "file")
        self.declare_parameter("file_path", "data/sample/en_zero.wav")
        self.declare_parameter("sample_rate_hz", 16000)
        self.declare_parameter("chunk_ms", 500)
        self.declare_parameter("loop_file", False)
        self.declare_parameter("mic_capture_sec", 4.0)
        self.declare_parameter("mic_device", "")
        self.declare_parameter("session_id", "")
        self.declare_parameter("autostart", False)

        self.configs_root = str(self.get_parameter("configs_root").value)
        self.runtime_profile = str(self.get_parameter("runtime_profile").value)
        self.input_mode = str(self.get_parameter("input_mode").value)
        self.file_path = str(self.get_parameter("file_path").value)
        self.sample_rate_hz = int(self.get_parameter("sample_rate_hz").value)
        self.chunk_ms = int(self.get_parameter("chunk_ms").value)
        self.loop_file = bool(self.get_parameter("loop_file").value)
        self.mic_capture_sec = float(self.get_parameter("mic_capture_sec").value)
        self.mic_device = str(self.get_parameter("mic_device").value)
        self.session_id = str(self.get_parameter("session_id").value).strip() or make_session_id()
        self.autostart = bool(self.get_parameter("autostart").value)

        self.publisher = self.create_publisher(AudioChunk, TOPICS["raw_audio"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)

        self.start_srv = self.create_service(
            StartRuntimeSession,
            "/asr/runtime/audio/start_session",
            self._on_start_session,
        )
        self.stop_srv = self.create_service(
            StopRuntimeSession,
            "/asr/runtime/audio/stop_session",
            self._on_stop_session,
        )
        self.reconfigure_srv = self.create_service(
            ReconfigureRuntime,
            "/asr/runtime/audio/reconfigure",
            self._on_reconfigure,
        )

        self._status = "idle"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._active = False
        self._shutdown = False

        self._load_runtime_configuration(self.runtime_profile, overrides={})
        self.status_timer = self.create_timer(1.0, self._publish_status)
        self._autostart_timer = self.create_timer(0.5, self._autostart_once) if self.autostart else None

    def _autostart_once(self) -> None:
        if self._autostart_timer is not None:
            self._autostart_timer.cancel()
            self._autostart_timer = None
        try:
            self._start_capture()
        except Exception as exc:
            self._set_error("audio_autostart_failed", str(exc))

    def _set_error(self, code: str, message: str) -> None:
        self._last_error_code = code
        self._last_error_message = message
        self._status = "error"
        self._last_update = self.get_clock().now()
        self.get_logger().error(message)

    def _load_runtime_configuration(self, runtime_profile: str, overrides: dict[str, object]) -> str:
        profile_id = runtime_profile
        if profile_id.startswith("runtime/"):
            profile_id = profile_id.split("/", 1)[1]

        resolved = resolve_profile(
            profile_type="runtime",
            profile_id=profile_id,
            configs_root=self.configs_root,
        )
        runtime_cfg = resolved.data
        errors = validate_runtime_payload(runtime_cfg)
        if errors:
            raise ValueError("; ".join(errors))

        audio_cfg = runtime_cfg.get("audio", {})
        if not isinstance(audio_cfg, dict):
            raise ValueError("runtime.audio must be an object")

        requested_source = str(overrides.get("audio_source", "") or audio_cfg.get("source", self.input_mode)).strip()
        requested_file = str(overrides.get("audio_file_path", "") or audio_cfg.get("file_path", self.file_path)).strip()
        requested_mic_capture = overrides.get("mic_capture_sec", 0.0)

        self.runtime_profile = profile_id
        self.input_mode = requested_source or "file"
        self.file_path = requested_file or self.file_path
        self.sample_rate_hz = int(audio_cfg.get("sample_rate_hz", self.sample_rate_hz) or self.sample_rate_hz)
        self.chunk_ms = int(audio_cfg.get("chunk_ms", self.chunk_ms) or self.chunk_ms)
        self.loop_file = bool(audio_cfg.get("loop_file", self.loop_file))
        if float(requested_mic_capture or 0.0) > 0.0:
            self.mic_capture_sec = float(requested_mic_capture)
        else:
            self.mic_capture_sec = float(audio_cfg.get("mic_capture_sec", self.mic_capture_sec) or self.mic_capture_sec)
        self.mic_device = str(audio_cfg.get("mic_device", self.mic_device) or "").strip()

        self._status = "ready"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        self.get_logger().info(
            f"Audio input configured: profile={self.runtime_profile} source={self.input_mode} file={self.file_path} mic_device={self.mic_device or 'default'}"
        )
        return resolved.snapshot_path

    def _is_running(self) -> bool:
        with self._lock:
            return self._worker is not None and self._worker.is_alive()

    def _start_capture(self) -> None:
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                raise RuntimeError("Audio session is already running")
            self._active = True
            self._status = "starting"
            self._worker = threading.Thread(target=self._capture_worker, daemon=True)
            self._worker.start()
        self._last_update = self.get_clock().now()

    def _stop_capture(self) -> bool:
        worker: threading.Thread | None = None
        with self._lock:
            self._active = False
            worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=max(self.mic_capture_sec + 2.0, 3.0))
        still_running = worker is not None and worker.is_alive()
        with self._lock:
            self._worker = worker if still_running else None
            if still_running:
                self._status = "stopping"
            else:
                self._status = "stopped"
                self._last_error_code = ""
                self._last_error_message = ""
        self._last_update = self.get_clock().now()
        return not still_running

    def _capture_worker(self) -> None:
        self._status = "running"
        self._last_update = self.get_clock().now()
        try:
            if self.input_mode in {"mic", "auto"}:
                if self._publish_mic_stream():
                    return
                if self.input_mode == "mic":
                    raise RuntimeError("Microphone capture failed")
                self.get_logger().warning("Microphone unavailable, switching to file fallback")
            self._publish_file_stream()
        except Exception as exc:
            self._set_error("audio_input_failure", str(exc))
        finally:
            with self._lock:
                if self._status == "running":
                    self._status = "completed"
                self._active = False
                self._worker = None
            self._last_update = self.get_clock().now()

    def _publish_file_stream(self) -> None:
        wav_path = Path(self.file_path)
        if not wav_path.exists():
            raise FileNotFoundError(f"Audio file not found: {wav_path}")

        while True:
            with wave.open(str(wav_path), "rb") as wf:
                if int(wf.getsampwidth()) != 2:
                    raise RuntimeError(
                        f"Unsupported WAV sample width for runtime file input: {wf.getsampwidth()} bytes"
                    )
                if str(wf.getcomptype()) != "NONE":
                    raise RuntimeError(
                        f"Unsupported WAV compression for runtime file input: {wf.getcomptype()}"
                    )

                file_sample_rate = int(wf.getframerate())
                file_channels = int(wf.getnchannels())
                frames_per_chunk = max(1, int(file_sample_rate * (self.chunk_ms / 1000.0)))
                index = 0
                while self._active:
                    data = wf.readframes(frames_per_chunk)
                    if not data:
                        self._publish_chunk(
                            b"",
                            is_last=True,
                            source_id=str(wav_path),
                            chunk_index=index,
                            sample_rate_hz=file_sample_rate,
                            channels=file_channels,
                        )
                        break
                    self._publish_chunk(
                        data,
                        is_last=False,
                        source_id=str(wav_path),
                        chunk_index=index,
                        sample_rate_hz=file_sample_rate,
                        channels=file_channels,
                    )
                    index += 1
            if not self.loop_file or not self._active:
                break

    def _publish_mic_stream(self) -> bool:
        try:
            import sounddevice as sd
        except Exception as exc:
            self.get_logger().warning(f"sounddevice import failed: {exc}")
            return False

        audio_q: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, callback_time, status) -> None:
            del frames, callback_time
            if status:
                self.get_logger().warning(f"Microphone callback status: {status}")
            if self._active:
                audio_q.put(bytes(indata))

        chunk_frames = max(1, int(self.sample_rate_hz * (self.chunk_ms / 1000.0)))
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate_hz,
                blocksize=chunk_frames,
                channels=1,
                dtype="int16",
                device=(self.mic_device or None),
                callback=callback,
            ):
                index = 0
                self.get_logger().info(f"Microphone capture active on device={self.mic_device or 'default'}")
                while self._active:
                    try:
                        data = audio_q.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    self._publish_chunk(
                        data,
                        is_last=False,
                        source_id="mic",
                        chunk_index=index,
                        sample_rate_hz=int(self.sample_rate_hz),
                        channels=1,
                    )
                    index += 1
                self._publish_chunk(
                    b"",
                    is_last=True,
                    source_id="mic",
                    chunk_index=index,
                    sample_rate_hz=int(self.sample_rate_hz),
                    channels=1,
                )
            return True
        except Exception as exc:
            self.get_logger().warning(f"Microphone capture failed: {exc}")
            return False

    def _publish_chunk(
        self,
        data: bytes,
        *,
        is_last: bool,
        source_id: str,
        chunk_index: int,
        sample_rate_hz: int,
        channels: int,
    ) -> None:
        msg = AudioChunk()
        msg.session_id = self.session_id
        msg.source_id = source_id
        msg.sample_rate = int(sample_rate_hz)
        msg.channels = int(channels)
        msg.encoding = "pcm_s16le"
        msg.is_last_chunk = bool(is_last)
        msg.data = list(data)
        msg.metadata_ref = f"chunk:{chunk_index}"
        msg.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(msg)
        self._last_update = self.get_clock().now()

    def _on_start_session(self, request: StartRuntimeSession.Request, response: StartRuntimeSession.Response):
        try:
            if self._is_running():
                raise RuntimeError("Audio input already has an active session")

            requested_session_id = str(request.session_id).strip()
            if requested_session_id and requested_session_id.lower() not in {"none", "null"}:
                self.session_id = requested_session_id
            else:
                self.session_id = make_session_id()

            overrides = {
                "audio_source": request.audio_source,
                "audio_file_path": request.audio_file_path,
                "mic_capture_sec": float(request.mic_capture_sec),
            }
            snapshot_path = self._load_runtime_configuration(request.runtime_profile or self.runtime_profile, overrides)

            if request.auto_start_audio:
                self._start_capture()

            response.accepted = True
            response.session_id = self.session_id
            response.message = "Audio session started"
            response.resolved_config_ref = snapshot_path
        except Exception as exc:
            response.accepted = False
            response.session_id = self.session_id
            response.message = str(exc)
            self._set_error("audio_start_failed", str(exc))
        return response

    def _on_stop_session(self, request: StopRuntimeSession.Request, response: StopRuntimeSession.Response):
        requested_session_id = str(request.session_id).strip()
        if (
            requested_session_id
            and requested_session_id.lower() not in {"none", "null"}
            and requested_session_id != self.session_id
        ):
            response.success = False
            response.message = "Session ID mismatch"
            return response

        if not self._stop_capture():
            self._set_error("audio_stop_timeout", "Audio input is still stopping")
            response.success = False
            response.message = "Audio input is still stopping"
            return response
        response.success = True
        response.message = "Audio session stopped"
        return response

    def _on_reconfigure(self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response):
        try:
            if self._is_running():
                raise RuntimeError("Cannot reconfigure audio input while session is running")

            overrides = {
                "audio_source": request.audio_source,
                "audio_file_path": request.audio_file_path,
                "mic_capture_sec": float(request.mic_capture_sec),
            }
            snapshot_path = self._load_runtime_configuration(request.runtime_profile or self.runtime_profile, overrides)
            response.success = True
            response.message = "Audio input reconfigured"
            response.resolved_config_ref = snapshot_path
        except Exception as exc:
            response.success = False
            response.message = str(exc)
            response.resolved_config_ref = ""
            self._set_error("audio_reconfigure_failed", str(exc))
        return response

    def _publish_status(self) -> None:
        msg = NodeStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.node_name = self.get_name()
        msg.lifecycle_state = "active"
        msg.health = "ok" if not self._last_error_code else "degraded"
        msg.status_message = f"{self._status} source={self.input_mode} session={self.session_id}"
        msg.ready = self._status in {"ready", "running", "completed", "stopped"}
        msg.last_error_code = self._last_error_code
        msg.last_error_message = self._last_error_message
        msg.last_update = self._last_update.to_msg()
        self.node_status_pub.publish(msg)

    def destroy_node(self) -> bool:
        self._shutdown = True
        self._stop_capture()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = AudioInputNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
