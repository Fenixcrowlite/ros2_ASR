from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest
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
        self.processing_mode = "segmented"
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


class _FailingErrorPublishOrchestrator:
    def __init__(self) -> None:
        self.provider = type("P", (), {"teardown": lambda self: None})()
        self.provider_id = "whisper"
        self.session_id = "s1"
        self.session_state = "running"
        self.audio_session_active = True
        self.session_ended_at = None
        self.session_updated_at = None
        self._stream_active = True
        self._stream_request_id = "stream_req"
        self._stop_requested_at = object()
        self.last_error_code = ""
        self.last_error_message = ""
        self.stopped_sessions = []
        self._clock = _FakeClock()

    def get_clock(self) -> _FakeClock:
        return self._clock

    def _publish_runtime_error_result(self, **kwargs) -> None:
        del kwargs
        raise RuntimeError("result bus unavailable")

    def _stop_audio_session(self, session_id: str) -> None:
        self.stopped_sessions.append(session_id)


class _NonStreamingProvider:
    provider_id = "batch_only"

    def __init__(self) -> None:
        self.teardown_calls = 0

    def discover_capabilities(self):
        return SimpleNamespace(supports_streaming=False)

    def teardown(self) -> None:
        self.teardown_calls += 1


class _ConfigProviderManager:
    def __init__(self, provider: _NonStreamingProvider) -> None:
        self.provider = provider
        self.calls = []

    def create_from_profile(self, provider_profile: str, *, preset_id: str = "", settings_overrides=None):
        self.calls.append(
            {
                "provider_profile": provider_profile,
                "preset_id": preset_id,
                "settings_overrides": dict(settings_overrides or {}),
            }
        )
        return self.provider


class _ConfigNode:
    def __init__(self, provider: _NonStreamingProvider) -> None:
        self.configs_root = "configs"
        self.runtime_profile = "default_runtime"
        self.provider_profile = ""
        self.provider_preset = ""
        self.provider_settings_overrides = {}
        self.processing_mode = "segmented"
        self.language = "en-US"
        self.enable_partials = True
        self.audio_source = "file"
        self.max_concurrent_sessions = 1
        self.provider_manager = _ConfigProviderManager(provider)
        self.provider = None
        self.provider_id = ""
        self._stream_active = False
        self._stream_request_id = ""

    def _require_object_mapping(self, value: object, label: str) -> dict[str, object]:
        return AsrOrchestratorNode._require_object_mapping(value, label)

    def _normalize_provider_settings(self, value: object) -> dict[str, object]:
        return AsrOrchestratorNode._normalize_provider_settings(value)

    def _resolve_runtime_profile_id(self, runtime_profile: str | None) -> str:
        return AsrOrchestratorNode._resolve_runtime_profile_id(self, runtime_profile)

    def _resolve_runtime_profile_sections(self, runtime_profile: str | None):
        return AsrOrchestratorNode._resolve_runtime_profile_sections(self, runtime_profile)

    def _resolve_runtime_configuration_target(
        self,
        overrides: dict[str, object],
        *,
        runtime_profile: str | None = None,
        provider_profile: str | None = None,
    ):
        return AsrOrchestratorNode._resolve_runtime_configuration_target(
            self,
            overrides,
            runtime_profile=runtime_profile,
            provider_profile=provider_profile,
        )

    def _apply_runtime_configuration_target(self, config) -> None:
        return AsrOrchestratorNode._apply_runtime_configuration_target(self, config)


class _StatusProvider:
    provider_id = "azure"

    def __init__(self, *, requires_network: bool, validation_errors: list[str]) -> None:
        self._requires_network = requires_network
        self._validation_errors = validation_errors

    def discover_capabilities(self):
        return SimpleNamespace(
            supports_streaming=True,
            streaming_mode="native",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_confidence=True,
            requires_network=self._requires_network,
        )

    def validate_config(self) -> list[str]:
        return list(self._validation_errors)


class _StatusNode:
    def __init__(self, provider: _StatusProvider | None) -> None:
        self.provider = provider
        self.provider_id = getattr(provider, "provider_id", "")
        self.provider_preset = "standard"
        self.session_state = "ready"
        self.session_id = "session_status"
        self.processing_mode = "segmented"
        self.audio_source = "file"
        self.runtime_profile = "default_runtime"


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


def test_handle_provider_runtime_failure_preserves_publish_failure_context() -> None:
    node = _FailingErrorPublishOrchestrator()

    AsrOrchestratorNode._handle_provider_runtime_failure(
        node,
        error_code="provider_stream_failed",
        error_message="provider exploded",
        request_id="req_1",
    )

    assert node.last_error_code == "provider_stream_failed"
    assert "provider exploded" in node.last_error_message
    assert "error_result_publish_failed: result bus unavailable" in node.last_error_message
    assert node.stopped_sessions == ["s1"]
    assert node.audio_session_active is False
    assert node._stream_active is False


def test_load_runtime_configuration_rejects_provider_stream_without_streaming_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _NonStreamingProvider()
    node = _ConfigNode(provider)
    monkeypatch.setattr(
        "asr_runtime_nodes.asr_orchestrator_node.resolve_profile",
        lambda **kwargs: SimpleNamespace(
            data={
                "orchestrator": {
                    "provider_profile": "providers/non_streaming",
                    "language": "en-US",
                    "processing_mode": "provider_stream",
                    "enable_partials": True,
                },
                "audio": {"source": "file"},
                "session": {"max_concurrent_sessions": 1},
            },
            snapshot_path="configs/resolved/runtime.json",
        ),
    )
    monkeypatch.setattr(
        "asr_runtime_nodes.asr_orchestrator_node.validate_runtime_payload",
        lambda payload: [],
    )

    with pytest.raises(ValueError, match="Provider does not support provider_stream mode"):
        AsrOrchestratorNode._load_runtime_configuration(node, overrides={})

    assert provider.teardown_calls == 1
    assert node.provider is None


def test_resolve_runtime_configuration_target_supports_providers_active_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _NonStreamingProvider()
    node = _ConfigNode(provider)
    monkeypatch.setattr(
        "asr_runtime_nodes.asr_orchestrator_node.resolve_profile",
        lambda **kwargs: SimpleNamespace(
            data={
                "orchestrator": {
                    "language": "en-US",
                    "processing_mode": "segmented",
                    "enable_partials": True,
                },
                "audio": {"source": "file"},
                "session": {"max_concurrent_sessions": 1},
                "providers": {
                    "active": "providers/huggingface_local",
                    "preset": "balanced",
                    "settings": {"device": "auto"},
                },
            },
            snapshot_path="configs/resolved/runtime_hf.json",
        ),
    )
    monkeypatch.setattr(
        "asr_runtime_nodes.asr_orchestrator_node.validate_runtime_payload",
        lambda payload: [],
    )

    config = AsrOrchestratorNode._resolve_runtime_configuration_target(
        node,
        {"provider_settings": {"torch_dtype": "float16"}},
        runtime_profile="runtime/huggingface_local_runtime",
    )

    assert config.provider_profile == "providers/huggingface_local"
    assert config.provider_preset == "balanced"
    assert config.provider_settings_overrides == {
        "device": "auto",
        "torch_dtype": "float16",
    }
    assert node.provider_manager.calls == [
        {
            "provider_profile": "providers/huggingface_local",
            "preset_id": "balanced",
            "settings_overrides": {
                "device": "auto",
                "torch_dtype": "float16",
            },
        }
    ]


def test_get_status_marks_cloud_credentials_unavailable_when_validation_fails() -> None:
    node = _StatusNode(_StatusProvider(requires_network=True, validation_errors=["missing credentials"]))
    response = SimpleNamespace()

    AsrOrchestratorNode._on_get_status(node, None, response)

    assert response.backend == "azure"
    assert response.streaming_mode == "native"
    assert response.cloud_credentials_available is False
    assert response.provider_runtime_ready is False


def test_get_status_marks_local_provider_ready_without_cloud_credentials() -> None:
    node = _StatusNode(_StatusProvider(requires_network=False, validation_errors=["ignored"]))
    response = SimpleNamespace()

    AsrOrchestratorNode._on_get_status(node, None, response)

    assert response.backend == "azure"
    assert response.cloud_credentials_available is True
    assert response.provider_runtime_ready is True
