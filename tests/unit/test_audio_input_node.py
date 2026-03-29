from __future__ import annotations

import wave
from pathlib import Path
from types import SimpleNamespace

import asr_runtime_nodes.audio_input_node as audio_input_node_module
import pytest
from asr_runtime_nodes.audio_input_node import AudioInputNode


class _FakeAudioInputNode:
    def __init__(self, wav_path: Path) -> None:
        self.file_path = str(wav_path)
        self.chunk_ms = 1000
        self.loop_file = True
        self._active = True
        self.published = []
        self.input_mode = "file"
        self.sample_rate_hz = 16000
        self.file_replay_rate = 0.0
        self.mic_capture_sec = 4.0
        self.mic_device = ""

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
        self.published.append(
            {
                "is_last": is_last,
                "source_id": source_id,
                "chunk_index": chunk_index,
                "sample_rate_hz": sample_rate_hz,
                "channels": channels,
                "size": len(data),
            }
        )
        if len(self.published) >= 2:
            self._active = False

    def get_logger(self):
        return SimpleNamespace(info=lambda message: message)


class _FakeConfigNode:
    def __init__(self) -> None:
        self.configs_root = "configs"
        self.runtime_profile = "default_runtime"
        self.input_mode = "file"
        self.file_path = "data/sample/vosk_test.wav"
        self.sample_rate_hz = 16000
        self.chunk_ms = 500
        self.loop_file = False
        self.file_replay_rate = 1.0
        self.mic_capture_sec = 4.0
        self.mic_device = ""
        self._status = "idle"
        self._last_error_code = ""
        self._last_error_message = ""
        self._last_update = SimpleNamespace()
        self._resolved_config_ref = "configs/resolved/runtime.json"

    def get_clock(self):
        return SimpleNamespace(now=lambda: SimpleNamespace())

    def get_logger(self):
        return SimpleNamespace(info=lambda message: message)


class _FakeStartNode:
    def __init__(self) -> None:
        self.runtime_profile = "default_runtime"
        self.input_mode = "file"
        self.file_path = "data/sample/vosk_test.wav"
        self.sample_rate_hz = 16000
        self.chunk_ms = 500
        self.loop_file = False
        self.file_replay_rate = 1.0
        self.mic_capture_sec = 4.0
        self.mic_device = ""
        self.session_id = "session-current"
        self._resolved_config_ref = "configs/resolved/runtime.json"
        self.loaded = []
        self.start_calls = 0
        self.errors = []
        self.warnings = []

    def _is_running(self) -> bool:
        return False

    def _load_runtime_configuration(self, runtime_profile: str, overrides: dict[str, object]) -> str:
        self.loaded.append((runtime_profile, overrides))
        self._resolved_config_ref = "configs/resolved/runtime_reloaded.json"
        return self._resolved_config_ref

    def _start_capture(self) -> None:
        self.start_calls += 1

    def _set_error(self, code: str, message: str) -> None:
        self.errors.append((code, message))

    def get_clock(self):
        return SimpleNamespace(now=lambda: SimpleNamespace())

    def get_logger(self):
        return SimpleNamespace(info=lambda message: message, warning=self.warnings.append)


class _FakeRunningStartNode(_FakeStartNode):
    def _is_running(self) -> bool:
        return True


def _write_wav(path: Path, *, frames: int = 1600, sample_rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)


def test_file_loop_mode_does_not_emit_terminal_chunk_between_iterations(tmp_path: Path) -> None:
    wav_path = tmp_path / "loop.wav"
    _write_wav(wav_path)
    node = _FakeAudioInputNode(wav_path)

    AudioInputNode._publish_file_stream(node)

    assert len(node.published) == 2
    assert [item["is_last"] for item in node.published] == [False, False]


def test_file_mode_replay_is_paced_when_replay_rate_is_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wav_path = tmp_path / "paced.wav"
    _write_wav(wav_path, frames=16000)
    node = _FakeAudioInputNode(wav_path)
    node.loop_file = False
    node.file_replay_rate = 2.0
    sleeps: list[float] = []
    monkeypatch.setattr(audio_input_node_module.time, "sleep", sleeps.append)

    AudioInputNode._publish_file_stream(node)

    assert len(node.published) == 2
    assert sleeps == [pytest.approx(0.5, abs=0.02)]


def test_load_runtime_configuration_rejects_invalid_audio_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = _FakeConfigNode()
    monkeypatch.setattr(
        "asr_runtime_nodes.audio_input_node.resolve_profile",
        lambda **kwargs: SimpleNamespace(
            data={
                "audio": {
                    "source": "bluetooth_telepathy",
                    "file_path": "data/sample/vosk_test.wav",
                    "sample_rate_hz": 16000,
                    "chunk_ms": 500,
                }
            },
            snapshot_path="configs/resolved/runtime.json",
        ),
    )
    monkeypatch.setattr(
        "asr_runtime_nodes.audio_input_node.validate_runtime_payload",
        lambda payload: [],
    )

    with pytest.raises(ValueError, match="Unsupported audio input mode"):
        AudioInputNode._load_runtime_configuration(
            node,
            "default_runtime",
            overrides={},
        )


def test_publish_mic_stream_raises_when_device_open_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = _FakeAudioInputNode(Path("data/sample/vosk_test.wav"))
    node._active = True

    class _BrokenRawInputStream:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        def __enter__(self):
            raise RuntimeError("no input device")

        def __exit__(self, exc_type, exc, tb) -> bool:
            del exc_type, exc, tb
            return False

    monkeypatch.setitem(
        __import__("sys").modules,
        "sounddevice",
        SimpleNamespace(RawInputStream=_BrokenRawInputStream),
    )

    with pytest.raises(RuntimeError, match="Microphone capture failed: no input device"):
        AudioInputNode._publish_mic_stream(node)


def test_load_runtime_configuration_rejects_negative_file_replay_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = _FakeConfigNode()
    monkeypatch.setattr(
        "asr_runtime_nodes.audio_input_node.resolve_profile",
        lambda **kwargs: SimpleNamespace(
            data={
                "audio": {
                    "source": "file",
                    "file_path": "data/sample/vosk_test.wav",
                    "sample_rate_hz": 16000,
                    "chunk_ms": 500,
                    "file_replay_rate": -1.0,
                }
            },
            snapshot_path="configs/resolved/runtime.json",
        ),
    )
    monkeypatch.setattr(
        "asr_runtime_nodes.audio_input_node.validate_runtime_payload",
        lambda payload: [],
    )

    with pytest.raises(ValueError, match="audio.file_replay_rate must be >= 0"):
        AudioInputNode._load_runtime_configuration(
            node,
            "default_runtime",
            overrides={},
        )


def test_start_session_reuses_loaded_configuration_when_request_matches_current_state() -> None:
    node = _FakeStartNode()
    request = SimpleNamespace(
        session_id="session-requested",
        runtime_profile="default_runtime",
        audio_source="",
        audio_file_path="",
        mic_capture_sec=0.0,
        auto_start_audio=True,
    )
    response = SimpleNamespace(accepted=False, session_id="", message="", resolved_config_ref="")

    AudioInputNode._on_start_session(node, request, response)

    assert response.accepted is True
    assert response.session_id == "session-requested"
    assert response.resolved_config_ref == "configs/resolved/runtime.json"
    assert node.loaded == []
    assert node.start_calls == 1


def test_start_session_reloads_configuration_when_audio_file_changes() -> None:
    node = _FakeStartNode()
    request = SimpleNamespace(
        session_id="session-requested",
        runtime_profile="default_runtime",
        audio_source="file",
        audio_file_path="data/sample/uploads/override.wav",
        mic_capture_sec=0.0,
        auto_start_audio=False,
    )
    response = SimpleNamespace(accepted=False, session_id="", message="", resolved_config_ref="")

    AudioInputNode._on_start_session(node, request, response)

    assert response.accepted is True
    assert response.resolved_config_ref == "configs/resolved/runtime_reloaded.json"
    assert node.loaded == [
        (
            "default_runtime",
            {
                "audio_source": "file",
                "audio_file_path": "data/sample/uploads/override.wav",
                "mic_capture_sec": 0.0,
            },
        )
    ]


def test_start_session_duplicate_active_request_is_idempotent() -> None:
    node = _FakeRunningStartNode()
    request = SimpleNamespace(
        session_id="session-current",
        runtime_profile="runtime/default_runtime",
        audio_source="file",
        audio_file_path="data/sample/../sample/vosk_test.wav",
        mic_capture_sec=4.0 + 1e-7,
        auto_start_audio=True,
    )
    response = SimpleNamespace(accepted=False, session_id="", message="", resolved_config_ref="")

    AudioInputNode._on_start_session(node, request, response)

    assert response.accepted is True
    assert response.session_id == "session-current"
    assert response.message == "Audio session already active"
    assert response.resolved_config_ref == "configs/resolved/runtime.json"
    assert node.loaded == []
    assert node.start_calls == 0
    assert node.errors == []
    assert any("Ignoring duplicate audio start request" in message for message in node.warnings)


def test_start_session_rejects_conflicting_active_request() -> None:
    node = _FakeRunningStartNode()
    request = SimpleNamespace(
        session_id="session-other",
        runtime_profile="default_runtime",
        audio_source="file",
        audio_file_path="data/sample/uploads/override.wav",
        mic_capture_sec=4.0,
        auto_start_audio=True,
    )
    response = SimpleNamespace(accepted=False, session_id="", message="", resolved_config_ref="")

    AudioInputNode._on_start_session(node, request, response)

    assert response.accepted is False
    assert "already has an active session" in response.message
    assert node.errors == [("audio_start_failed", "Audio input already has an active session")]
