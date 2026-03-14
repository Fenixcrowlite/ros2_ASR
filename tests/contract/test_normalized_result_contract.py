from __future__ import annotations

from tests.utils.fakes import make_normalized_result


def test_normalized_result_contract_explicitly_carries_availability_flags() -> None:
    result = make_normalized_result(provider_id="whisper")
    payload = result.as_dict()

    assert payload["confidence_available"] is True
    assert payload["timestamps_available"] is True
    assert payload["raw_metadata_ref"] == "artifact://fake/raw"
    assert payload["error_code"] == ""
    assert payload["error_message"] == ""
    assert isinstance(payload["words"], list)
