import pytest
from asr_core.factory import create_backend


def test_create_mock_backend() -> None:
    backend = create_backend("mock", config={})
    assert backend.name == "mock"


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError):
        create_backend("unknown")
