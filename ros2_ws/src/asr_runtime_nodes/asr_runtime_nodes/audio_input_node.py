"""Audio input node publishing raw chunks from microphone or file."""

from __future__ import annotations

import os
import queue
import threading
import time
import wave
from pathlib import Path
from typing import Any

import rclpy
from asr_config import resolve_profile, validate_runtime_payload
from asr_core.ids import make_session_id
from asr_core.namespaces import TOPICS
from asr_core.shutdown import safe_shutdown_node
from asr_interfaces.msg import AudioChunk, NodeStatus
from asr_interfaces.srv import ReconfigureRuntime, StartRuntimeSession, StopRuntimeSession
from rclpy.node import Node


class AudioInputNode(Node):
    @staticmethod
    def _as_float(value: object, default: float = 0.0) -> float:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_int(value: object, default: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    def __init__(self) -> None:
        super().__init__("audio_input_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("input_mode", "file")
        self.declare_parameter("file_path", "data/sample/vosk_test.wav")
        self.declare_parameter("sample_rate_hz", 16000)
        self.declare_parameter("chunk_ms", 500)
        self.declare_parameter("loop_file", False)
        self.declare_parameter("file_replay_rate", 1.0)
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
        self.file_replay_rate = float(self.get_parameter("file_replay_rate").value)
        self.mic_capture_sec = float(self.get_parameter("mic_capture_sec").value)
        self.mic_device = str(self.get_parameter("mic_device").value)
        self.session_id = str(self.get_parameter("session_id").value).strip() or make_session_id()
        self.autostart = bool(self.get_parameter("autostart").value)

        self.publisher = self.create_publisher(AudioChunk, TOPICS["raw_audio"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)

        # The orchestrator controls this source node through services rather
        # than direct function calls, so the stages stay loosely coupled.
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
        self._resolved_config_ref = ""
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._active = False
        self._shutdown = False

        self._load_runtime_configuration(self.runtime_profile, overrides={})
        self.status_timer = self.create_timer(1.0, self._publish_status)
        self._autostart_timer = (
            self.create_timer(0.5, self._autostart_once) if self.autostart else None
        )

    @staticmethod
    def _is_explicit_value(value: object) -> bool:
        text = str(value or "").strip()
        return bool(text) and text.lower() not in {"none", "null"}

    @staticmethod
    def _normalized_requested_value(value: object, current: str, *, default: str = "") -> str:
        return (
            str(value).strip() if AudioInputNode._is_explicit_value(value) else (current or default)
        )

    @staticmethod
    def _normalized_runtime_profile_id(value: object, current: str) -> str:
        profile_id = AudioInputNode._normalized_requested_value(value, current, default=current)
        if profile_id.startswith("runtime/"):
            profile_id = profile_id.split("/", 1)[1]
        return profile_id

    @staticmethod
    def _normalized_audio_file_path(value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        return Path(os.path.normpath(text)).as_posix()

    def _request_overrides(self, request: Any) -> dict[str, object]:
        return {
            "audio_source": getattr(request, "audio_source", ""),
            "audio_file_path": getattr(request, "audio_file_path", ""),
            "mic_capture_sec": float(getattr(request, "mic_capture_sec", 0.0) or 0.0),
        }

    @staticmethod
    def _request_matches_loaded_configuration(
        node, request: Any, overrides: dict[str, object]
    ) -> bool:
        requested_profile = AudioInputNode._normalized_runtime_profile_id(
            getattr(request, "runtime_profile", ""),
            str(node.runtime_profile),
        )
        requested_source = AudioInputNode._normalized_requested_value(
            overrides.get("audio_source", ""),
            str(node.input_mode),
            default="file",
        )
        requested_file = AudioInputNode._normalized_requested_value(
            overrides.get("audio_file_path", ""),
            str(node.file_path),
            default=str(node.file_path),
        )
        requested_mic_capture = AudioInputNode._as_float(overrides.get("mic_capture_sec", 0.0))
        effective_mic_capture = (
            requested_mic_capture
            if requested_mic_capture > 0.0
            else AudioInputNode._as_float(getattr(node, "mic_capture_sec", 0.0))
        )
        return (
            requested_profile == str(node.runtime_profile).strip()
            and requested_source == str(node.input_mode).strip()
            and AudioInputNode._normalized_audio_file_path(requested_file)
            == AudioInputNode._normalized_audio_file_path(node.file_path)
            and abs(
                effective_mic_capture
                - AudioInputNode._as_float(getattr(node, "mic_capture_sec", 0.0))
            )
            < 1e-6
        )

    @staticmethod
    def _same_start_request_as_active_session(
        node, request: Any, overrides: dict[str, object]
    ) -> bool:
        requested_session_id = AudioInputNode._normalized_requested_value(
            getattr(request, "session_id", ""),
            str(getattr(node, "session_id", "") or ""),
            default=str(getattr(node, "session_id", "") or ""),
        )
        current_session_id = str(getattr(node, "session_id", "") or "").strip()
        if not requested_session_id or requested_session_id != current_session_id:
            return False
        return AudioInputNode._request_matches_loaded_configuration(node, request, overrides)

    def _apply_audio_settings(
        self, audio_cfg: dict[str, object], overrides: dict[str, object]
    ) -> None:
        requested_source = AudioInputNode._normalized_requested_value(
            overrides.get("audio_source", ""),
            str(audio_cfg.get("source", self.input_mode)).strip(),
            default="file",
        )
        requested_file = AudioInputNode._normalized_requested_value(
            overrides.get("audio_file_path", ""),
            str(audio_cfg.get("file_path", self.file_path)).strip(),
            default=self.file_path,
        )
        requested_mic_capture = AudioInputNode._as_float(overrides.get("mic_capture_sec", 0.0))

        self.input_mode = requested_source
        self.file_path = requested_file
        self.sample_rate_hz = AudioInputNode._as_int(
            audio_cfg.get("sample_rate_hz", self.sample_rate_hz),
            self.sample_rate_hz,
        )
        self.chunk_ms = AudioInputNode._as_int(
            audio_cfg.get("chunk_ms", self.chunk_ms), self.chunk_ms
        )
        self.loop_file = bool(audio_cfg.get("loop_file", self.loop_file))
        self.file_replay_rate = AudioInputNode._as_float(
            audio_cfg.get("file_replay_rate", self.file_replay_rate),
            self.file_replay_rate,
        )
        self.mic_capture_sec = (
            requested_mic_capture
            if requested_mic_capture > 0.0
            else AudioInputNode._as_float(
                audio_cfg.get("mic_capture_sec", self.mic_capture_sec),
                self.mic_capture_sec,
            )
        )
        self.mic_device = str(audio_cfg.get("mic_device", self.mic_device) or "").strip()

    def _validate_audio_settings(self) -> None:
        if self.input_mode not in {"file", "mic"}:
            raise ValueError(f"Unsupported audio input mode: {self.input_mode}")
        if self.sample_rate_hz <= 0:
            raise ValueError("audio.sample_rate_hz must be > 0")
        if self.chunk_ms <= 0:
            raise ValueError("audio.chunk_ms must be > 0")
        if self.file_replay_rate < 0:
            raise ValueError("audio.file_replay_rate must be >= 0")
        if self.mic_capture_sec < 0:
            raise ValueError("audio.mic_capture_sec must be >= 0")
        if self.input_mode == "file" and not str(self.file_path).strip():
            raise ValueError("audio.file_path must be set when source=file")

    def _file_replay_delay_sec(
        self, *, payload_size_bytes: int, sample_rate_hz: int, channels: int
    ) -> float:
        replay_rate = float(self.file_replay_rate)
        if replay_rate <= 0.0 or payload_size_bytes <= 0:
            return 0.0
        bytes_per_second = max(int(sample_rate_hz) * max(int(channels), 1) * 2, 1)
        return max((payload_size_bytes / float(bytes_per_second)) / replay_rate, 0.0)

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

    def _load_runtime_configuration(
        self, runtime_profile: str, overrides: dict[str, object]
    ) -> str:
        # Runtime profile decides whether this node reads from a WAV file or
        # captures the microphone, plus the chunking/sample-rate behavior.
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

        self.runtime_profile = profile_id
        AudioInputNode._apply_audio_settings(self, audio_cfg, overrides)
        AudioInputNode._validate_audio_settings(self)

        self._status = "ready"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = self.get_clock().now()
        self._resolved_config_ref = resolved.snapshot_path
        self.get_logger().info(
            "Audio input configured: "
            f"profile={self.runtime_profile} "
            f"source={self.input_mode} "
            f"file={self.file_path} "
            f"mic_device={self.mic_device or 'default'}"
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
            if self.input_mode == "mic":
                self._publish_mic_stream()
            else:
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
        # File mode turns one WAV into a stream of AudioChunk messages so the
        # rest of pipeline can treat file and microphone input the same way.
        wav_path = Path(self.file_path)
        if not wav_path.exists():
            raise FileNotFoundError(f"Audio file not found: {wav_path}")

        while True:
            with wave.open(str(wav_path), "rb") as wf:
                if int(wf.getsampwidth()) != 2:
                    raise RuntimeError(
                        "Unsupported WAV sample width for runtime file input: "
                        f"{wf.getsampwidth()} bytes"
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
                        if not self.loop_file or not self._active:
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
                    replay_delay_sec = AudioInputNode._file_replay_delay_sec(
                        self,
                        payload_size_bytes=len(data),
                        sample_rate_hz=file_sample_rate,
                        channels=file_channels,
                    )
                    if self._active and replay_delay_sec > 0.0:
                        time.sleep(replay_delay_sec)
                    index += 1
            if not self.loop_file or not self._active:
                break

    def _publish_mic_stream(self) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:
            raise RuntimeError(f"sounddevice import failed: {exc}") from exc

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
                self.get_logger().info(
                    f"Microphone capture active on device={self.mic_device or 'default'}"
                )
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
        except Exception as exc:
            raise RuntimeError(f"Microphone capture failed: {exc}") from exc

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

    def _on_start_session(
        self, request: StartRuntimeSession.Request, response: StartRuntimeSession.Response
    ):
        try:
            overrides = AudioInputNode._request_overrides(self, request)
            if self._is_running():
                if AudioInputNode._same_start_request_as_active_session(self, request, overrides):
                    response.accepted = True
                    response.session_id = self.session_id
                    response.message = "Audio session already active"
                    response.resolved_config_ref = str(getattr(self, "_resolved_config_ref", ""))
                    self._last_error_code = ""
                    self._last_error_message = ""
                    self._last_update = self.get_clock().now()
                    self.get_logger().warning(
                        "Ignoring duplicate audio start request for active session "
                        f"{self.session_id}"
                    )
                    return response
                raise RuntimeError("Audio input already has an active session")

            self.session_id = AudioInputNode._normalized_requested_value(
                request.session_id,
                "",
                default=make_session_id(),
            )

            if AudioInputNode._request_matches_loaded_configuration(self, request, overrides):
                snapshot_path = str(getattr(self, "_resolved_config_ref", ""))
            else:
                snapshot_path = self._load_runtime_configuration(
                    request.runtime_profile or self.runtime_profile,
                    overrides,
                )

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

    def _on_stop_session(
        self, request: StopRuntimeSession.Request, response: StopRuntimeSession.Response
    ):
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

    def _on_reconfigure(
        self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response
    ):
        try:
            if self._is_running():
                raise RuntimeError("Cannot reconfigure audio input while session is running")

            overrides = AudioInputNode._request_overrides(self, request)
            snapshot_path = self._load_runtime_configuration(
                request.runtime_profile or self.runtime_profile, overrides
            )
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
