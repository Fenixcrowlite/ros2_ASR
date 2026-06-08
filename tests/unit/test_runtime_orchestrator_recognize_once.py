from __future__ import annotations

from types import SimpleNamespace

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_runtime_nodes.asr_orchestrator_node import AsrOrchestratorNode


class _BaseProvider:
    provider_id = "whisper"

    def teardown(self) -> None:
        return None


class _StableProvider(_BaseProvider):
    def recognize_once(self, audio):
        return NormalizedAsrResult(
            request_id=audio.request_id,
            session_id=audio.session_id,
            provider_id="whisper",
            text="ok",
            is_final=True,
            is_partial=False,
            language=audio.language,
            latency=LatencyMetadata(total_ms=25.0, first_partial_ms=0.0, finalization_ms=1.0),
        )


class _ExplodingTempProvider(_BaseProvider):
    def __init__(self) -> None:
        self.teardown_calls = 0

    def recognize_once(self, audio):
        del audio
        raise RuntimeError("temporary provider exploded")

    def teardown(self) -> None:
        self.teardown_calls += 1


class _FakeProviderManager:
    def __init__(self, temp_provider: _ExplodingTempProvider) -> None:
        self.temp_provider = temp_provider
        self.calls = []

    def create_from_profile(
        self,
        provider_profile: str,
        *,
        preset_id: str = "",
        settings_overrides=None,
    ):
        self.calls.append(
            {
                "provider_profile": provider_profile,
                "preset_id": preset_id,
                "settings_overrides": dict(settings_overrides or {}),
            }
        )
        return self.temp_provider


class _ResolvedTempProvider(_BaseProvider):
    provider_id = "azure"

    def recognize_once(self, audio):
        return NormalizedAsrResult(
            request_id=audio.request_id,
            session_id=audio.session_id,
            provider_id="azure",
            text="cloud ok",
            is_final=True,
            is_partial=False,
            language=audio.language,
            latency=LatencyMetadata(total_ms=42.0, first_partial_ms=0.0, finalization_ms=2.0),
        )


class _ResolvingProviderManager:
    def __init__(self) -> None:
        self.calls = []

    def create_from_profile(
        self,
        provider_profile: str,
        *,
        preset_id: str = "",
        settings_overrides=None,
    ):
        self.calls.append(
            {
                "provider_profile": provider_profile,
                "preset_id": preset_id,
                "settings_overrides": dict(settings_overrides or {}),
            }
        )
        return _ResolvedTempProvider()


class _FakeClock:
    def __init__(self) -> None:
        self._tick = 0

    def now(self):
        self._tick += 1
        return SimpleNamespace(
            nanoseconds=self._tick * 100_000_000,
            to_msg=lambda: SimpleNamespace(sec=0, nanosec=self._tick * 100_000_000),
        )


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.provider = _StableProvider()
        self.provider_profile = "providers/whisper_local"
        self.provider_manager = None
        self.session_id = "session_demo"
        self.language = "en-US"
        self.last_error_code = ""
        self.last_error_message = ""
        self.session_updated_at = None
        self.published = []
        self._clock = _FakeClock()

    def get_clock(self):
        return self._clock

    def _publish_result(self, result) -> None:
        self.published.append(result)

    def _build_overrides_from_request(self, request):
        return AsrOrchestratorNode._build_overrides_from_request(self, request)

    def _choose_requested_value(self, requested, current, *, default=""):
        return AsrOrchestratorNode._choose_requested_value(
            self,
            requested,
            current,
            default=default,
        )

    def _read_recognize_audio_bytes(self, wav_path: str) -> bytes:
        return AsrOrchestratorNode._read_recognize_audio_bytes(self, wav_path)

    def _resolve_recognize_provider(
        self,
        *,
        provider_profile: str,
        provider_preset: str,
        provider_settings: dict[str, object],
    ):
        return AsrOrchestratorNode._resolve_recognize_provider(
            self,
            provider_profile=provider_profile,
            provider_preset=provider_preset,
            provider_settings=provider_settings,
        )

    def _copy_result_message(self, source, target) -> None:
        target.request_id = getattr(source, "request_id", "")
        target.text = getattr(source, "text", "")
        target.provider_id = getattr(source, "provider_id", "")
        target.success = getattr(source, "success", True)
        target.language = getattr(source, "language", "")


def _make_response():
    return SimpleNamespace(
        result=SimpleNamespace(success=True, error_code="", error_message=""),
        resolved_profile="",
    )


def test_recognize_once_tears_down_temporary_provider_on_failure() -> None:
    node = _FakeOrchestrator()
    temp_provider = _ExplodingTempProvider()
    node.provider_manager = _FakeProviderManager(temp_provider)
    request = SimpleNamespace(
        wav_path="",
        language="en-US",
        session_id="session_demo",
        enable_word_timestamps=True,
        provider_profile="",
        provider_preset="accurate",
        provider_settings_json='{"beam_size": 5}',
    )
    response = _make_response()

    result = AsrOrchestratorNode._on_recognize_once(node, request, response)

    assert result.result.success is False
    assert result.result.error_code == "recognize_once_failed"
    assert "temporary provider exploded" in result.result.error_message
    assert result.resolved_profile == "providers/whisper_local"
    assert temp_provider.teardown_calls == 1
    assert node.last_error_code == "recognize_once_failed"
    assert node.published == []


def test_recognize_once_honors_provider_profile_override() -> None:
    node = _FakeOrchestrator()
    node.provider_manager = _ResolvingProviderManager()
    request = SimpleNamespace(
        wav_path="",
        language="en-US",
        session_id="session_demo",
        enable_word_timestamps=True,
        provider_profile="providers/azure_cloud",
        provider_preset="",
        provider_settings_json="{}",
    )
    response = _make_response()

    result = AsrOrchestratorNode._on_recognize_once(node, request, response)

    assert result.result.success is True
    assert result.result.provider_id == "azure"
    assert result.result.text == "cloud ok"
    assert result.resolved_profile == "providers/azure_cloud"
    assert node.provider_manager.calls == [
        {
            "provider_profile": "providers/azure_cloud",
            "preset_id": "",
            "settings_overrides": {},
        }
    ]
