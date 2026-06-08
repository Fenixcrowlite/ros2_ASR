from __future__ import annotations

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord


def test_normalized_result_as_dict_preserves_contract_fields() -> None:
    result = NormalizedAsrResult(
        request_id="req_1",
        session_id="session_1",
        provider_id="whisper",
        text="hello world",
        is_final=True,
        is_partial=False,
        utterance_start_sec=0.0,
        utterance_end_sec=0.8,
        words=[
            NormalizedWord("hello", 0.0, 0.4, 0.91, True),
            NormalizedWord("world", 0.41, 0.8, 0.94, True),
        ],
        confidence=0.93,
        confidence_available=True,
        timestamps_available=True,
        language="en-US",
        language_detected=False,
        latency=LatencyMetadata(total_ms=22.0, first_partial_ms=7.0, finalization_ms=5.0),
        raw_metadata_ref="artifact://raw/req_1",
        degraded=False,
        error_code="",
        error_message="",
        tags=["baseline"],
    )

    payload = result.as_dict()

    assert payload["request_id"] == "req_1"
    assert payload["session_id"] == "session_1"
    assert payload["provider_id"] == "whisper"
    assert payload["latency"]["total_ms"] == 22.0
    assert payload["words"][0]["word"] == "hello"
    assert payload["confidence_available"] is True
    assert payload["timestamps_available"] is True
