from __future__ import annotations

from array import array
from collections import defaultdict, deque
from dataclasses import dataclass

from asr_interfaces.msg import AudioChunk
from asr_runtime_nodes.audio_preprocess_node import AudioPreprocessNode
from asr_runtime_nodes.vad_segmenter_node import VadSegmenterNode


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
    def __init__(self, values_ms: list[int]):
        self._values = [_FakeTime(value * 1_000_000) for value in values_ms]
        self._index = 0

    def now(self) -> _FakeTime:
        if self._index >= len(self._values):
            return self._values[-1]
        value = self._values[self._index]
        self._index += 1
        return value


class _Collector:
    def __init__(self) -> None:
        self.items = []

    def publish(self, msg) -> None:
        self.items.append(msg)


class _FakePreprocessNode:
    def __init__(self) -> None:
        self.force_mono = True
        self.target_sample_rate_hz = 16000
        self.normalize = True
        self.publisher = _Collector()
        self._session_output_rate = defaultdict(lambda: self.target_sample_rate_hz)
        self._session_output_channels = defaultdict(lambda: 1)
        self._last_raw_sequence = defaultdict(lambda: -1)
        self._raw_chunks_in = 0
        self._raw_chunks_out = 0
        self._raw_sequence_gaps = 0
        self._last_raw_delivery_ms = 0.0
        self._max_raw_delivery_ms = 0.0
        self._status = "idle"
        self._last_update = _FakeTime(0)
        self._clock = _FakeClock([0, 100])

    def get_clock(self) -> _FakeClock:
        return self._clock


class _FakeVadNode:
    def __init__(self) -> None:
        self.energy_threshold = 50
        self.pre_roll_ms = 250
        self.max_silence_ms = 700
        self.min_segment_ms = 400
        self.max_segment_ms = 2500
        self.activity_pub = _Collector()
        self.segment_pub = _Collector()
        self._buffers = defaultdict(bytearray)
        self._segment_start = {}
        self._segment_elapsed_ms = defaultdict(int)
        self._trailing_silence_ms = defaultdict(int)
        self._segment_index = defaultdict(int)
        self._segment_sample_rate = {}
        self._segment_channels = {}
        self._segment_encoding = {}
        self._segment_source_id = {}
        self._segment_metadata_ref = {}
        self._pre_roll_chunks = defaultdict(deque)
        self._pre_roll_total_ms = defaultdict(int)
        self._segment_chunk_count = defaultdict(int)
        self._segment_gap_count = defaultdict(int)
        self._last_preprocessed_sequence = defaultdict(lambda: -1)
        self._preprocessed_chunks_in = 0
        self._segments_out = 0
        self._preprocessed_sequence_gaps = 0
        self._last_preprocessed_delivery_ms = 0.0
        self._max_preprocessed_delivery_ms = 0.0
        self._status = "idle"
        self._last_update = _FakeTime(0)
        self._clock = _FakeClock([0, 500, 1000, 1001])

    def get_clock(self) -> _FakeClock:
        return self._clock

    def _pcm_duration_ms(self, msg, payload: bytes) -> int:
        return VadSegmenterNode._pcm_duration_ms(self, msg, payload)

    def _append_pre_roll(self, msg, payload: bytes) -> None:
        VadSegmenterNode._append_pre_roll(self, msg, payload)

    def _consume_pre_roll(self, session_id: str) -> bytes:
        return VadSegmenterNode._consume_pre_roll(self, session_id)

    def _clear_pre_roll(self, session_id: str) -> None:
        VadSegmenterNode._clear_pre_roll(self, session_id)

    def _flush_segment(self, msg, end_time, *, reason: str = "threshold") -> None:
        VadSegmenterNode._flush_segment(self, msg, end_time, reason=reason)


def _make_chunk(
    *,
    session_id: str,
    sample_rate: int,
    channels: int,
    data: bytes,
    is_last: bool,
    metadata_ref: str,
) -> AudioChunk:
    msg = AudioChunk()
    msg.session_id = session_id
    msg.source_id = "test-source"
    msg.sample_rate = sample_rate
    msg.channels = channels
    msg.encoding = "pcm_s16le"
    msg.is_last_chunk = is_last
    msg.data = list(data)
    msg.metadata_ref = metadata_ref
    return msg


def test_preprocess_terminal_chunk_preserves_output_format() -> None:
    node = _FakePreprocessNode()

    speech = _make_chunk(
        session_id="s1",
        sample_rate=8000,
        channels=1,
        data=(b"\x10\x00" * 2000),
        is_last=False,
        metadata_ref="chunk:0",
    )
    end = _make_chunk(
        session_id="s1",
        sample_rate=8000,
        channels=1,
        data=b"",
        is_last=True,
        metadata_ref="chunk:1",
    )

    AudioPreprocessNode._on_chunk(node, speech)
    AudioPreprocessNode._on_chunk(node, end)

    assert len(node.publisher.items) == 2
    first, last = node.publisher.items
    assert isinstance(first.data, array)
    assert isinstance(last.data, array)
    assert int(first.sample_rate) == 16000
    assert int(last.sample_rate) == 16000
    assert int(last.channels) == 1


def test_vad_flush_uses_segment_stream_metadata_not_terminal_marker() -> None:
    node = _FakeVadNode()

    speech_a = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 8000),
        is_last=False,
        metadata_ref="chunk:0",
    )
    speech_b = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 2400),
        is_last=False,
        metadata_ref="chunk:1",
    )
    terminal = _make_chunk(
        session_id="s1",
        sample_rate=8000,
        channels=1,
        data=b"",
        is_last=True,
        metadata_ref="chunk:2",
    )

    VadSegmenterNode._on_chunk(node, speech_a)
    VadSegmenterNode._on_chunk(node, speech_b)
    VadSegmenterNode._on_chunk(node, terminal)

    assert len(node.segment_pub.items) == 1
    segment = node.segment_pub.items[0]
    assert isinstance(segment.data, array)
    assert int(segment.sample_rate) == 16000
    assert int(segment.channels) == 1
    assert bytes(segment.data) == bytes(speech_a.data) + bytes(speech_b.data)


def test_vad_includes_pre_roll_to_preserve_speech_onset() -> None:
    node = _FakeVadNode()
    node.min_segment_ms = 50
    node.pre_roll_ms = 250

    pre_roll = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\x10\x00" * 2400),
        is_last=False,
        metadata_ref="chunk:0",
    )
    speech = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 4800),
        is_last=False,
        metadata_ref="chunk:1",
    )
    terminal = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=b"",
        is_last=True,
        metadata_ref="chunk:2",
    )

    VadSegmenterNode._on_chunk(node, pre_roll)
    VadSegmenterNode._on_chunk(node, speech)
    VadSegmenterNode._on_chunk(node, terminal)

    assert len(node.segment_pub.items) == 1
    segment = node.segment_pub.items[0]
    assert bytes(segment.data).startswith(bytes(pre_roll.data))
    assert bytes(segment.data).endswith(bytes(speech.data))


def test_vad_flush_respects_u8_sample_width_when_estimating_segment_duration() -> None:
    node = _FakeVadNode()
    node.min_segment_ms = 120
    node._buffers["s1"].extend(b"\xff" * 1200)
    node._segment_start["s1"] = _FakeTime(0)
    node._segment_elapsed_ms["s1"] = 150
    node._segment_sample_rate["s1"] = 8000
    node._segment_channels["s1"] = 1
    node._segment_encoding["s1"] = "pcm_u8"
    node._segment_source_id["s1"] = "u8-source"
    node._segment_metadata_ref["s1"] = "chunk:u8"

    terminal = _make_chunk(
      session_id="s1",
      sample_rate=8000,
      channels=1,
      data=b"",
      is_last=True,
      metadata_ref="chunk:u8-terminal",
    )
    terminal.encoding = "pcm_u8"

    VadSegmenterNode._flush_segment(node, terminal, _FakeTime(150 * 1_000_000))

    assert len(node.segment_pub.items) == 1
    segment = node.segment_pub.items[0]
    assert segment.encoding == "pcm_u8"
    assert bytes(segment.data) == b"\xff" * 1200


def test_vad_flushes_file_mode_segment_on_audio_silence_not_wall_clock() -> None:
    node = _FakeVadNode()
    node.min_segment_ms = 100
    node.max_silence_ms = 700
    node._clock = _FakeClock([0, 1, 2, 3, 4, 5])

    speech = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 3200),
        is_last=False,
        metadata_ref="chunk:0",
    )
    silence = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\x00\x00" * 12800),
        is_last=False,
        metadata_ref="chunk:1",
    )

    VadSegmenterNode._on_chunk(node, speech)
    VadSegmenterNode._on_chunk(node, silence)

    assert len(node.segment_pub.items) == 1
    segment = node.segment_pub.items[0]
    assert bytes(segment.data) == bytes(speech.data)


def test_vad_flushes_file_mode_segment_on_audio_duration_not_wall_clock() -> None:
    node = _FakeVadNode()
    node.min_segment_ms = 100
    node.max_segment_ms = 300
    node._clock = _FakeClock([0, 1, 2, 3, 4, 5])

    speech_a = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 3200),
        is_last=False,
        metadata_ref="chunk:0",
    )
    speech_b = _make_chunk(
        session_id="s1",
        sample_rate=16000,
        channels=1,
        data=(b"\xff\x7f" * 3200),
        is_last=False,
        metadata_ref="chunk:1",
    )

    VadSegmenterNode._on_chunk(node, speech_a)
    VadSegmenterNode._on_chunk(node, speech_b)

    assert len(node.segment_pub.items) == 1
    segment = node.segment_pub.items[0]
    assert bytes(segment.data) == bytes(speech_a.data) + bytes(speech_b.data)
