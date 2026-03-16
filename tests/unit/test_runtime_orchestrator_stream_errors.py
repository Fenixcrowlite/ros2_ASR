from __future__ import annotations

from dataclasses import dataclass

from asr_interfaces.msg import AudioChunk
from asr_runtime_nodes.asr_orchestrator_node import AsrOrchestratorNode


@dataclass
class _FakeTime:
    nanoseconds: int

    def to_msg(self):
        class _Stamp:
            sec = 0
            nanosec = 0

        stamp = _Stamp()
        stamp.sec = self.nanoseconds // 1_000_000_000
        stamp.nanosec = self.nanoseconds % 1_000_000_000
        return stamp


class _FakeClock:
    def __init__(self) -> None:
        self._now = 0

    def now(self) -> _FakeTime:
        self._now += 100_000_000
        return _FakeTime(self._now)


class _ExplodingStreamProvider:
    provider_id = "vosk"

    def discover_capabilities(self):
        class _Caps:
            supports_streaming = True

        return _Caps()

    def start_stream(self, options=None) -> None:
        raise RuntimeError("Vosk model is not configured or failed to load: model directory is empty")

    def teardown(self) -> None:
        return None


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.processing_mode = "provider_stream"
        self.session_id = "s1"
        self.provider = _ExplodingStreamProvider()
        self.provider_id = "vosk"
        self.language = "ru-RU"
        self.enable_partials = True
        self.session_state = "ready"
        self.audio_session_active = True
        self.session_updated_at = _FakeTime(0)
        self.session_ended_at = None
        self.last_error_code = ""
        self.last_error_message = ""
        self._stream_active = False
        self._stream_request_id = ""
        self._stop_requested_at = None
        self._clock = _FakeClock()
        self.published = []
        self.stop_calls = 0

    def get_clock(self) -> _FakeClock:
        return self._clock

    def _publish_result(self, result) -> None:
        self.published.append(result)
        self.last_error_code = result.error_code
        self.last_error_message = result.error_message
        self.session_updated_at = self.get_clock().now()

    def _stop_audio_session(self, session_id: str) -> None:
        assert session_id == "s1"
        self.stop_calls += 1

    def _publish_runtime_error_result(self, *, request_id: str, error_code: str, error_message: str) -> None:
        return AsrOrchestratorNode._publish_runtime_error_result(
            self,
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
        )

    def _handle_provider_runtime_failure(self, *, error_code: str, error_message: str, request_id: str = "") -> None:
        return AsrOrchestratorNode._handle_provider_runtime_failure(
            self,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )


def test_streaming_provider_exception_does_not_kill_orchestrator() -> None:
    node = _FakeOrchestrator()
    chunk = AudioChunk()
    chunk.session_id = "s1"
    chunk.sample_rate = 16000
    chunk.channels = 1
    chunk.encoding = "pcm_s16le"
    chunk.data = list(b"\x01\x00" * 200)
    chunk.is_last_chunk = False

    AsrOrchestratorNode._on_preprocessed_chunk(node, chunk)

    assert node.session_state == "error"
    assert node.audio_session_active is False
    assert node.stop_calls == 1
    assert node.last_error_code == "provider_stream_error"
    assert "Vosk model is not configured or failed to load" in node.last_error_message
    assert len(node.published) == 1
    assert node.published[0].degraded is True
    assert node.published[0].error_code == "provider_stream_error"
