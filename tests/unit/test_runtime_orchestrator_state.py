from __future__ import annotations

from dataclasses import dataclass

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_interfaces.msg import AudioSegment
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


class _SequenceProvider:
    def __init__(self) -> None:
        self.calls = 0

    def recognize_once(self, audio):
        self.calls += 1
        if self.calls == 1:
            return NormalizedAsrResult(
                request_id=audio.request_id,
                session_id=audio.session_id,
                provider_id="whisper",
                text="",
                is_final=True,
                is_partial=False,
                language="en-US",
                latency=LatencyMetadata(total_ms=50.0, first_partial_ms=0.0, finalization_ms=1.0),
                degraded=True,
                error_code="empty_transcript",
                error_message="empty",
            )
        return NormalizedAsrResult(
            request_id=audio.request_id,
            session_id=audio.session_id,
            provider_id="whisper",
            text="hello world",
            is_final=True,
            is_partial=False,
            language="en-US",
            latency=LatencyMetadata(total_ms=50.0, first_partial_ms=0.0, finalization_ms=1.0),
        )


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.session_id = "s1"
        self.session_state = "degraded"
        self.provider = _SequenceProvider()
        self.language = "en-US"
        self.session_updated_at = _FakeTime(0)
        self.session_ended_at = None
        self._stop_requested_at = None
        self.last_error_code = "empty_transcript"
        self.last_error_message = "empty"
        self._clock = _FakeClock()
        self.published = []

    def get_clock(self) -> _FakeClock:
        return self._clock

    def _publish_result(self, result) -> None:
        self.published.append(result)
        self.last_error_code = result.error_code
        self.last_error_message = result.error_message
        self.session_updated_at = self.get_clock().now()


def test_orchestrator_accepts_new_segments_after_degraded_result() -> None:
    node = _FakeOrchestrator()
    segment = AudioSegment()
    segment.session_id = "s1"
    segment.sample_rate = 16000
    segment.channels = 1
    segment.encoding = "pcm_s16le"
    segment.data = list(b"\x01\x00" * 1000)

    AsrOrchestratorNode._on_segment(node, segment)

    assert len(node.published) == 1
    assert node.published[0].text == ""
    assert node.session_state == "ready"

    AsrOrchestratorNode._on_segment(node, segment)

    assert len(node.published) == 2
    assert node.published[1].text == "hello world"
    assert node.session_state == "ready"
    assert node.last_error_code == ""
