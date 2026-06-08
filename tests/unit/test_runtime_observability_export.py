from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_interfaces.msg import AudioChunk, AudioSegment
from asr_observability import FileTraceExporter, ObservabilityConfig
from asr_runtime_nodes.asr_orchestrator_node import AsrOrchestratorNode
from asr_runtime_nodes.transport import encode_transport_metadata


class _FakeTime:
    def __init__(self, nanoseconds: int) -> None:
        self.nanoseconds = nanoseconds

    def to_msg(self):
        return SimpleNamespace(
            sec=self.nanoseconds // 1_000_000_000,
            nanosec=self.nanoseconds % 1_000_000_000,
        )


class _FakeClock:
    def __init__(self) -> None:
        self._now = 2_000_000_000

    def now(self) -> _FakeTime:
        self._now += 100_000_000
        return _FakeTime(self._now)


class _Collector:
    def __init__(self) -> None:
        self.items = []

    def publish(self, msg) -> None:
        self.items.append(msg)


class _Logger:
    def info(self, message: str) -> None:
        del message

    def warning(self, message: str) -> None:
        del message


class _SegmentProvider:
    provider_id = "whisper"

    def __init__(self) -> None:
        self._asr_model_load_ms = 12.5
        self._asr_provider_init_cold_start = True

    def recognize_once(self, audio) -> NormalizedAsrResult:
        return NormalizedAsrResult(
            request_id=audio.request_id,
            session_id=audio.session_id,
            provider_id=self.provider_id,
            text="segment ok",
            is_final=True,
            is_partial=False,
            language=audio.language,
            audio_duration_sec=0.48,
            confidence=0.91,
            confidence_available=True,
            latency=LatencyMetadata(
                total_ms=42.0,
                preprocess_ms=10.0,
                inference_ms=28.0,
                postprocess_ms=4.0,
            ),
        )

    def teardown(self) -> None:
        return None


class _StreamingProvider:
    provider_id = "vosk"

    def __init__(self) -> None:
        self._chunks = 0
        self._session_id = "s1"
        self._request_id = "req_stream"
        self._asr_model_load_ms = 5.0
        self._asr_provider_init_cold_start = True

    def discover_capabilities(self):
        return SimpleNamespace(supports_streaming=True)

    def start_stream(self, options=None) -> None:
        opts = options or {}
        self._session_id = str(opts.get("session_id", "s1") or "s1")
        self._request_id = str(opts.get("request_id", "req_stream") or "req_stream")

    def push_audio(self, chunk: bytes):
        self._chunks += 1
        if self._chunks == 1:
            return NormalizedAsrResult(
                request_id=self._request_id,
                session_id=self._session_id,
                provider_id=self.provider_id,
                text="partial one",
                is_final=False,
                is_partial=True,
                language="en-US",
                confidence=0.0,
                confidence_available=False,
                timestamps_available=False,
                latency=LatencyMetadata(total_ms=15.0, first_partial_ms=15.0),
            )
        del chunk
        return None

    def drain_stream_results(self) -> list[NormalizedAsrResult]:
        return []

    def stop_stream(self) -> NormalizedAsrResult:
        return NormalizedAsrResult(
            request_id=self._request_id,
            session_id=self._session_id,
            provider_id=self.provider_id,
            text="stream final",
            is_final=True,
            is_partial=False,
            language="en-US",
            audio_duration_sec=0.64,
            confidence=0.82,
            confidence_available=True,
            latency=LatencyMetadata(
                total_ms=60.0,
                preprocess_ms=5.0,
                inference_ms=50.0,
                postprocess_ms=5.0,
                first_partial_ms=15.0,
            ),
        )

    def teardown(self) -> None:
        return None


class _BaseTraceNode:
    def __init__(self, *, artifact_root: Path, provider, processing_mode: str) -> None:
        self.provider = provider
        self.provider_id = provider.provider_id
        self.provider_profile = f"providers/{provider.provider_id}_profile"
        self.runtime_profile = "default_runtime"
        self.processing_mode = processing_mode
        self.audio_source = "file"
        self.language = "en-US"
        self.enable_partials = True
        self.session_id = "session_obs"
        self.session_state = "ready"
        self.audio_session_active = True
        self.session_started_at = _FakeTime(0)
        self.session_updated_at = _FakeTime(0)
        self.session_ended_at = None
        self.last_error_code = ""
        self.last_error_message = ""
        self._stream_active = False
        self._stream_request_id = ""
        self._stream_trace_state = None
        self._stop_requested_at = None
        self._clock = _FakeClock()
        self.final_pub = _Collector()
        self.partial_pub = _Collector()
        self._observability_config = ObservabilityConfig(
            artifact_root=str(artifact_root),
            export_json=True,
            export_csv=True,
            include_system_metrics=False,
            include_gpu_metrics=False,
        )
        self._trace_exporter = FileTraceExporter(self._observability_config)
        self._logger = _Logger()

    def get_clock(self) -> _FakeClock:
        return self._clock

    def get_name(self) -> str:
        return "asr_orchestrator_node"

    def get_logger(self) -> _Logger:
        return self._logger

    def _publish_result(self, result) -> None:
        return AsrOrchestratorNode._publish_result(self, result)

    def _publish_partial_result(self, result) -> None:
        return AsrOrchestratorNode._publish_partial_result(self, result)

    def _log_excerpt(self, value: object, *, limit: int = 160) -> str:
        return AsrOrchestratorNode._log_excerpt(value, limit=limit)

    def _export_runtime_trace(self, trace) -> str:
        return AsrOrchestratorNode._export_runtime_trace(self, trace)

    def _stop_audio_session(self, session_id: str) -> None:
        del session_id


class _SegmentTraceNode(_BaseTraceNode):
    def __init__(self, *, artifact_root: Path) -> None:
        super().__init__(
            artifact_root=artifact_root,
            provider=_SegmentProvider(),
            processing_mode="segmented",
        )

    def _handle_provider_runtime_failure(self, *, error_code: str, error_message: str, request_id: str = "") -> None:
        return AsrOrchestratorNode._handle_provider_runtime_failure(
            self,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )


class _StreamingTraceNode(_BaseTraceNode):
    def __init__(self, *, artifact_root: Path) -> None:
        super().__init__(
            artifact_root=artifact_root,
            provider=_StreamingProvider(),
            processing_mode="provider_stream",
        )

    def _should_accept_stream_chunk(self, msg) -> bool:
        return AsrOrchestratorNode._should_accept_stream_chunk(self, msg)

    def _stream_start_options(self, msg):
        return AsrOrchestratorNode._stream_start_options(self, msg)

    def _ensure_provider_stream_started(self, msg) -> None:
        return AsrOrchestratorNode._ensure_provider_stream_started(self, msg)

    def _forward_stream_audio(self, msg) -> None:
        return AsrOrchestratorNode._forward_stream_audio(self, msg)

    def _finish_provider_stream(self) -> None:
        return AsrOrchestratorNode._finish_provider_stream(self)

    def _handle_stream_update(self, result) -> None:
        return AsrOrchestratorNode._handle_stream_update(self, result)

    def _handle_provider_runtime_failure(self, *, error_code: str, error_message: str, request_id: str = "") -> None:
        return AsrOrchestratorNode._handle_provider_runtime_failure(
            self,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )

    def _publish_runtime_error_result(
        self,
        *,
        request_id: str,
        error_code: str,
        error_message: str,
        raw_metadata_ref: str = "",
    ) -> None:
        del raw_metadata_ref
        return AsrOrchestratorNode._publish_runtime_error_result(
            self,
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
        )


def test_segmented_runtime_exports_trace_artifact(tmp_path: Path) -> None:
    node = _SegmentTraceNode(artifact_root=tmp_path / "artifacts")
    segment = AudioSegment()
    segment.session_id = "session_obs"
    segment.segment_id = "session_obs_seg_0"
    segment.source_id = "file"
    segment.sample_rate = 16000
    segment.channels = 1
    segment.encoding = "pcm_s16le"
    segment.data = list(b"\x01\x00" * 800)
    segment.metadata_ref = "chunk:5"
    segment.header.stamp = _FakeTime(1_900_000_000).to_msg()
    segment.header.frame_id = encode_transport_metadata(
        {
            "stage": "speech_segments",
            "segment_sequence": 5,
            "segment_chunk_count": 4,
            "sequence_gap_count": 2,
        }
    )

    AsrOrchestratorNode._on_segment(node, segment)

    metrics_dir = tmp_path / "artifacts" / "runtime_sessions" / "session_obs" / "metrics"
    trace_files = list(metrics_dir.glob("trace_*.json"))
    assert len(trace_files) == 1
    payload = json.loads(trace_files[0].read_text(encoding="utf-8"))
    assert payload["trace_type"] == "runtime_segment"
    assert payload["metrics"]["chunk_count"] == 4
    assert payload["metrics"]["sequence_gap_count"] == 2
    assert payload["metrics"]["provider_call_cold_start"] is True
    assert payload["metrics"]["model_load_ms"] == 12.5
    assert node.final_pub.items[0].raw_metadata_ref == str(trace_files[0])
    assert (metrics_dir / "trace_index.csv").exists()


def test_provider_stream_runtime_exports_trace_artifact(tmp_path: Path) -> None:
    node = _StreamingTraceNode(artifact_root=tmp_path / "artifacts")

    first = AudioChunk()
    first.session_id = "session_obs"
    first.sample_rate = 16000
    first.channels = 1
    first.encoding = "pcm_s16le"
    first.data = list(b"\x01\x00" * 400)
    first.is_last_chunk = False
    first.header.stamp = _FakeTime(1_900_000_000).to_msg()
    first.header.frame_id = encode_transport_metadata(
        {
            "stage": "preprocessed_audio",
            "preprocessed_sequence": 1,
            "sequence_gap_count": 0,
        }
    )

    second = AudioChunk()
    second.session_id = "session_obs"
    second.sample_rate = 16000
    second.channels = 1
    second.encoding = "pcm_s16le"
    second.data = list(b"\x02\x00" * 400)
    second.is_last_chunk = True
    second.header.stamp = _FakeTime(2_000_000_000).to_msg()
    second.header.frame_id = encode_transport_metadata(
        {
            "stage": "preprocessed_audio",
            "preprocessed_sequence": 2,
            "sequence_gap_count": 1,
        }
    )

    AsrOrchestratorNode._on_preprocessed_chunk(node, first)
    AsrOrchestratorNode._on_preprocessed_chunk(node, second)

    metrics_dir = tmp_path / "artifacts" / "runtime_sessions" / "session_obs" / "metrics"
    trace_files = list(metrics_dir.glob("trace_*.json"))
    assert len(trace_files) == 1
    payload = json.loads(trace_files[0].read_text(encoding="utf-8"))
    assert payload["trace_type"] == "runtime_provider_stream"
    assert payload["metrics"]["chunk_count"] == 2
    assert payload["metrics"]["sequence_gap_count"] == 1
    assert payload["metrics"]["time_to_first_result_ms"] == 15.0
    assert payload["metrics"]["provider_call_cold_start"] is True
    assert payload["metrics"]["model_load_ms"] == 5.0
    assert len(node.partial_pub.items) == 1
    assert node.final_pub.items[-1].raw_metadata_ref == str(trace_files[0])
    assert (metrics_dir / "trace_index.csv").exists()
