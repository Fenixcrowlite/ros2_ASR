from __future__ import annotations

import threading
import time
from types import SimpleNamespace

from asr_ros.asr_server_node import AsrServerNode


class _FakeLogger:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def test_streaming_not_supported_response_is_explicit() -> None:
    fake_node = SimpleNamespace(backend_name="whisper", model="tiny", region="local")

    response = AsrServerNode._streaming_not_supported_response(
        fake_node,
        language="en-US",
        error_code="action_streaming_not_supported",
    )

    assert response.success is False
    assert response.error_code == "action_streaming_not_supported"
    assert "does not support streaming" in response.error_message
    assert response.backend_info["provider"] == "whisper"


def test_live_timer_emits_explicit_error_for_batch_only_backend() -> None:
    logger = _FakeLogger()
    captured: dict[str, object] = {}

    def _unexpected_stream_call(*args, **kwargs):
        del args, kwargs
        raise AssertionError("streaming_recognize should not be called for batch-only backend")

    fake_node = SimpleNamespace(
        live_stream_enabled=True,
        _live_lock=threading.Lock(),
        _live_chunks=[b"\x00\x00" * 100],
        _live_last_chunk_ts=time.monotonic() - 2.0,
        _live_capture_start=None,
        _live_capture_end=None,
        _live_processing=False,
        live_flush_timeout_sec=0.1,
        lock=threading.Lock(),
        backend=SimpleNamespace(
            capabilities=SimpleNamespace(supports_streaming=False),
            streaming_recognize=_unexpected_stream_call,
        ),
        language="en-US",
        sample_rate=16000,
        backend_name="whisper",
        model="tiny",
        region="local",
        _streaming_not_supported_response=lambda *, language, error_code: AsrServerNode._streaming_not_supported_response(
            SimpleNamespace(backend_name="whisper", model="tiny", region="local"),
            language=language,
            error_code=error_code,
        ),
        _publish_response_and_metrics=lambda response, **kwargs: captured.setdefault("response", response),
        get_logger=lambda: logger,
    )

    AsrServerNode._on_live_timer(fake_node)

    response = captured["response"]
    assert response.error_code == "live_streaming_not_supported"
    assert response.success is False
    assert "does not support streaming" in response.error_message
    assert any("Live transcription failed" in message for message in logger.warnings)
