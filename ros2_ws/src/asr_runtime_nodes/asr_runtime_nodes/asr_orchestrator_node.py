"""ASR orchestrator node selecting provider adapters and coordinating runtime pipeline."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import rclpy
from asr_config import list_profiles, resolve_profile, validate_runtime_payload
from asr_core import TOPICS, make_request_id, make_session_id
from asr_core.audio import sample_width_from_encoding, wav_duration_sec
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_core.shutdown import safe_shutdown_node, spin_node_until_shutdown
from asr_interfaces.msg import (
    AsrResult,
    AsrResultPartial,
    AudioChunk,
    AudioSegment,
    NodeStatus,
    SessionStatus,
)
from asr_interfaces.srv import (
    GetAsrStatus,
    ListBackends,
    ListProfiles,
    RecognizeOnce,
    ReconfigureRuntime,
    StartRuntimeSession,
    StopRuntimeSession,
    ValidateConfig,
)
from asr_provider_base import ProviderAudio, ProviderManager, list_providers
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

from metrics import FileTraceExporter, PipelineTraceCollector, build_runtime_trace, load_observability_config

from asr_runtime_nodes.converters import to_asr_result_msg, to_partial_msg


@dataclass(slots=True)
class RuntimeStateSnapshot:
    runtime_profile: str
    provider_profile: str
    session_id: str
    session_state: str
    session_started_at: Any
    session_updated_at: Any
    session_ended_at: Any
    last_error_code: str
    last_error_message: str
    audio_source: str
    language: str
    enable_partials: bool
    max_concurrent_sessions: int
    provider: Any
    provider_id: str
    provider_preset: str
    provider_settings_overrides: dict[str, object]
    processing_mode: str
    audio_session_active: bool
    stream_active: bool
    stream_request_id: str
    stop_requested_at: Any


@dataclass(slots=True)
class ResolvedRuntimeConfiguration:
    snapshot_path: str
    runtime_profile: str
    provider_profile: str
    provider_preset: str
    provider_settings_overrides: dict[str, object]
    processing_mode: str
    language: str
    enable_partials: bool
    audio_source: str
    max_concurrent_sessions: int
    provider: Any


class AsrOrchestratorNode(Node):
    def __init__(self) -> None:
        super().__init__("asr_orchestrator_node")
        self.declare_parameter("configs_root", "configs")
        self.declare_parameter("runtime_profile", "default_runtime")
        self.declare_parameter("provider_profile", "")
        self.declare_parameter("session_id", "")

        self.configs_root = str(self.get_parameter("configs_root").value)
        self.runtime_profile = str(self.get_parameter("runtime_profile").value)
        self.provider_profile = str(self.get_parameter("provider_profile").value)
        self.session_id = str(self.get_parameter("session_id").value).strip() or make_session_id()
        self.session_state = "idle"
        self.audio_session_active = False
        self._stop_requested_at = None
        self.session_started_at = self.get_clock().now()
        self.session_updated_at = self.session_started_at
        self.session_ended_at = None
        self.last_error_code = ""
        self.last_error_message = ""

        # ProviderManager turns human-readable YAML profiles into ready-to-use
        # provider adapters, including preset merging and secret resolution.
        self.provider_manager = ProviderManager(configs_root=self.configs_root)
        self.provider = None
        self.provider_id = ""
        self.provider_preset = ""
        self.provider_settings_overrides: dict[str, object] = {}
        self.processing_mode = "segmented"
        self.language = "en-US"
        self.enable_partials = True
        self.audio_source = "file"
        self.max_concurrent_sessions = 1
        self._stream_active = False
        self._stream_request_id = ""
        try:
            self._observability_config = load_observability_config(configs_root=self.configs_root)
            self._trace_exporter = FileTraceExporter(self._observability_config)
        except Exception as exc:
            self._observability_config = None
            self._trace_exporter = None
            self.get_logger().warning(f"Observability config unavailable: {exc}")
        self._load_runtime_configuration(overrides={})

        # Final/partial result topics are the main outward-facing runtime data
        # contract for gateway, tests, and future subscribers.
        retained_result_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.final_pub = self.create_publisher(
            AsrResult, TOPICS["final_results"], retained_result_qos
        )
        self.partial_pub = self.create_publisher(AsrResultPartial, TOPICS["partial_results"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)
        self.session_status_pub = self.create_publisher(SessionStatus, TOPICS["session_status"], 10)

        # The orchestrator can work in two modes:
        # 1. segmented: consume VAD-produced AudioSegment messages;
        # 2. provider_stream: consume preprocessed chunks directly.
        self.segment_sub = self.create_subscription(
            AudioSegment,
            TOPICS["speech_segments"],
            self._on_segment,
            10,
        )
        self.chunk_sub = self.create_subscription(
            AudioChunk,
            TOPICS["preprocessed_audio"],
            self._on_preprocessed_chunk,
            10,
        )

        # These services are the public control plane used by gateway/UI.
        self.start_srv = self.create_service(
            StartRuntimeSession,
            "/asr/runtime/start_session",
            self._on_start_session,
        )
        self.stop_srv = self.create_service(
            StopRuntimeSession,
            "/asr/runtime/stop_session",
            self._on_stop_session,
        )
        self.reconfigure_srv = self.create_service(
            ReconfigureRuntime,
            "/asr/runtime/reconfigure",
            self._on_reconfigure,
        )
        self.recognize_srv = self.create_service(
            RecognizeOnce,
            "/asr/runtime/recognize_once",
            self._on_recognize_once,
        )
        self.list_profiles_srv = self.create_service(
            ListProfiles,
            "/config/list_profiles",
            self._on_list_profiles,
        )
        self.list_backends_srv = self.create_service(
            ListBackends,
            "/asr/runtime/list_backends",
            self._on_list_backends,
        )
        self.validate_srv = self.create_service(
            ValidateConfig,
            "/config/validate",
            self._on_validate,
        )
        self.status_srv = self.create_service(
            GetAsrStatus, "/asr/runtime/get_status", self._on_get_status
        )

        self.status_timer = self.create_timer(1.0, self._publish_status)
        self.session_state = "ready"

    @staticmethod
    def _is_explicit_value(value: object) -> bool:
        text = str(value or "").strip()
        return bool(text) and text.lower() not in {"none", "null"}

    def _choose_requested_value(self, requested: object, current: str, *, default: str = "") -> str:
        return (
            str(requested).strip()
            if AsrOrchestratorNode._is_explicit_value(requested)
            else (current or default)
        )

    def _snapshot_runtime_state(self) -> RuntimeStateSnapshot:
        return RuntimeStateSnapshot(
            runtime_profile=self.runtime_profile,
            provider_profile=self.provider_profile,
            session_id=self.session_id,
            session_state=self.session_state,
            session_started_at=self.session_started_at,
            session_updated_at=self.session_updated_at,
            session_ended_at=self.session_ended_at,
            last_error_code=self.last_error_code,
            last_error_message=self.last_error_message,
            audio_source=self.audio_source,
            language=self.language,
            enable_partials=self.enable_partials,
            max_concurrent_sessions=self.max_concurrent_sessions,
            provider=self.provider,
            provider_id=self.provider_id,
            provider_preset=self.provider_preset,
            provider_settings_overrides=dict(self.provider_settings_overrides),
            processing_mode=self.processing_mode,
            audio_session_active=self.audio_session_active,
            stream_active=self._stream_active,
            stream_request_id=self._stream_request_id,
            stop_requested_at=self._stop_requested_at,
        )

    def _restore_runtime_state(self, snapshot: RuntimeStateSnapshot) -> None:
        self.runtime_profile = snapshot.runtime_profile
        self.provider_profile = snapshot.provider_profile
        self.session_id = snapshot.session_id
        self.session_state = snapshot.session_state
        self.session_started_at = snapshot.session_started_at
        self.session_updated_at = snapshot.session_updated_at
        self.session_ended_at = snapshot.session_ended_at
        self.last_error_code = snapshot.last_error_code
        self.last_error_message = snapshot.last_error_message
        self.audio_source = snapshot.audio_source
        self.language = snapshot.language
        self.enable_partials = snapshot.enable_partials
        self.max_concurrent_sessions = snapshot.max_concurrent_sessions
        self.provider = snapshot.provider
        self.provider_id = snapshot.provider_id
        self.provider_preset = snapshot.provider_preset
        self.provider_settings_overrides = dict(snapshot.provider_settings_overrides)
        self.processing_mode = snapshot.processing_mode
        self.audio_session_active = snapshot.audio_session_active
        self._stream_active = snapshot.stream_active
        self._stream_request_id = snapshot.stream_request_id
        self._stop_requested_at = snapshot.stop_requested_at

    def _build_overrides_from_request(self, request) -> dict[str, object]:
        # Normalize optional ROS request fields into one dict so start,
        # reconfigure, and recognize-once share the same parsing logic.
        provider_settings_json = str(getattr(request, "provider_settings_json", "") or "").strip()
        provider_settings: dict[str, object] = {}
        if provider_settings_json:
            parsed = json.loads(provider_settings_json)
            if not isinstance(parsed, dict):
                raise ValueError("provider_settings_json must be a JSON object")
            provider_settings = parsed
        return {
            "audio_source": str(getattr(request, "audio_source", "") or "").strip(),
            "audio_file_path": str(getattr(request, "audio_file_path", "") or "").strip(),
            "language": str(getattr(request, "language", "") or "").strip(),
            "mic_capture_sec": float(getattr(request, "mic_capture_sec", 0.0) or 0.0),
            "processing_mode": str(getattr(request, "processing_mode", "") or "").strip(),
            "provider_preset": str(getattr(request, "provider_preset", "") or "").strip(),
            "provider_settings": provider_settings,
        }

    @staticmethod
    def _require_object_mapping(value: object, label: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError(f"{label} must be an object")
        return dict(value)

    @staticmethod
    def _normalize_provider_settings(value: object) -> dict[str, object]:
        if value and not isinstance(value, dict):
            raise ValueError("provider_settings must be an object")
        if not value:
            return {}
        return dict(cast(dict[str, object], value))

    @staticmethod
    def _coerce_float(value: object, default: float = 0.0) -> float:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_int(value: object, default: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _active_provider(self):
        if self.provider is None:
            raise RuntimeError("Provider is not initialized")
        return self.provider

    def _resolve_runtime_profile_id(self, runtime_profile: str | None) -> str:
        runtime_profile_id = str(runtime_profile or self.runtime_profile or "").strip()
        if runtime_profile_id.startswith("runtime/"):
            runtime_profile_id = runtime_profile_id.split("/", 1)[1]
        return runtime_profile_id

    def _resolve_runtime_profile_sections(
        self,
        runtime_profile: str | None,
    ) -> tuple[str, str, dict[str, object], dict[str, object], dict[str, object]]:
        runtime_profile_id = self._resolve_runtime_profile_id(runtime_profile)
        runtime_cfg = resolve_profile(
            profile_type="runtime",
            profile_id=runtime_profile_id,
            configs_root=self.configs_root,
        )
        errors = validate_runtime_payload(runtime_cfg.data)
        if errors:
            raise ValueError(f"Runtime profile validation failed: {'; '.join(errors)}")

        orchestrator_cfg = self._require_object_mapping(
            runtime_cfg.data.get("orchestrator", {}),
            "runtime.orchestrator",
        )
        audio_cfg = self._require_object_mapping(runtime_cfg.data.get("audio", {}), "runtime.audio")
        session_cfg = self._require_object_mapping(
            runtime_cfg.data.get("session", {}), "runtime.session"
        )
        return (
            runtime_profile_id,
            runtime_cfg.snapshot_path,
            orchestrator_cfg,
            audio_cfg,
            session_cfg,
        )

    def _resolve_runtime_configuration_target(
        self,
        overrides: dict[str, object],
        *,
        runtime_profile: str | None = None,
        provider_profile: str | None = None,
    ) -> ResolvedRuntimeConfiguration:
        (
            runtime_profile_id,
            snapshot_path,
            orchestrator_cfg,
            audio_cfg,
            session_cfg,
        ) = self._resolve_runtime_profile_sections(runtime_profile)

        target_provider_profile = str(
            provider_profile or self.provider_profile or ""
        ).strip() or str(orchestrator_cfg.get("provider_profile", "providers/whisper_local"))
        requested_provider_preset = str(overrides.get("provider_preset", "") or "").strip()
        requested_provider_settings = self._normalize_provider_settings(
            overrides.get("provider_settings", {})
        )
        target_language = str(overrides.get("language", "") or "").strip() or str(
            orchestrator_cfg.get("language", "en-US")
        )
        target_processing_mode = str(overrides.get("processing_mode", "") or "").strip() or str(
            orchestrator_cfg.get("processing_mode", "segmented")
        )
        if target_processing_mode not in {"segmented", "provider_stream"}:
            raise ValueError(f"Unsupported processing_mode: {target_processing_mode}")

        provider = self.provider_manager.create_from_profile(
            target_provider_profile,
            preset_id=requested_provider_preset,
            settings_overrides=requested_provider_settings,
        )
        if target_processing_mode == "provider_stream":
            caps = provider.discover_capabilities()
            if not caps.supports_streaming:
                try:
                    provider.teardown()
                except Exception as exc:
                    raise ValueError(
                        "Provider does not support provider_stream mode: "
                        f"{target_provider_profile}; cleanup failed: {exc}"
                    ) from exc
                raise ValueError(
                    f"Provider does not support provider_stream mode: {target_provider_profile}"
                )

        return ResolvedRuntimeConfiguration(
            snapshot_path=snapshot_path,
            runtime_profile=runtime_profile_id,
            provider_profile=target_provider_profile,
            provider_preset=requested_provider_preset,
            provider_settings_overrides=requested_provider_settings,
            processing_mode=target_processing_mode,
            language=target_language,
            enable_partials=bool(orchestrator_cfg.get("enable_partials", True)),
            audio_source=str(overrides.get("audio_source", "") or "").strip()
            or str(audio_cfg.get("source", "file")),
            max_concurrent_sessions=self._coerce_int(
                session_cfg.get("max_concurrent_sessions", 1),
                1,
            ),
            provider=provider,
        )

    def _apply_runtime_configuration_target(self, config: ResolvedRuntimeConfiguration) -> None:
        previous_provider = self.provider
        self.runtime_profile = config.runtime_profile
        self.provider_profile = config.provider_profile
        self.provider_preset = config.provider_preset
        self.provider_settings_overrides = dict(config.provider_settings_overrides)
        self.processing_mode = config.processing_mode
        self.language = config.language
        self.enable_partials = config.enable_partials
        self.audio_source = config.audio_source
        self.max_concurrent_sessions = config.max_concurrent_sessions
        self.provider = config.provider
        self.provider_id = config.provider.provider_id
        self._stream_active = False
        self._stream_request_id = ""
        if previous_provider is not None and previous_provider is not config.provider:
            previous_provider.teardown()

    def _load_runtime_configuration(
        self,
        overrides: dict[str, object],
        *,
        runtime_profile: str | None = None,
        provider_profile: str | None = None,
    ) -> str:
        config = self._resolve_runtime_configuration_target(
            overrides,
            runtime_profile=runtime_profile,
            provider_profile=provider_profile,
        )
        self._apply_runtime_configuration_target(config)
        return config.snapshot_path

    def _call_service(self, service_type, service_name: str, request, timeout_sec: float = 5.0):
        # The orchestrator coordinates sibling runtime nodes over ROS services
        # so each stage remains independently launchable and testable.
        temp_node = Node(
            f"asr_orchestrator_client_{uuid.uuid4().hex[:8]}", use_global_arguments=False
        )
        try:
            client = temp_node.create_client(service_type, service_name)
            if not client.wait_for_service(timeout_sec=timeout_sec):
                raise RuntimeError(f"Service unavailable: {service_name}")
            future = client.call_async(request)
            executor = SingleThreadedExecutor()
            executor.add_node(temp_node)
            deadline_ns = self.get_clock().now().nanoseconds + int(timeout_sec * 1_000_000_000)
            while not future.done():
                remaining_ns = deadline_ns - self.get_clock().now().nanoseconds
                if remaining_ns <= 0:
                    raise RuntimeError(f"Timed out waiting for service: {service_name}")
                executor.spin_once(timeout_sec=min(0.2, remaining_ns / 1_000_000_000.0))
            result = future.result()
            if result is None:
                raise RuntimeError(f"No response from service: {service_name}")
            return result
        finally:
            temp_node.destroy_node()

    def _populate_runtime_stage_request(
        self,
        request: Any,
        *,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
        overrides: dict[str, object],
        runtime_namespace: str = "",
        auto_start_audio: bool | None = None,
    ) -> None:
        request.session_id = session_id
        request.runtime_profile = runtime_profile
        request.provider_profile = provider_profile
        if hasattr(request, "processing_mode"):
            request.processing_mode = str(overrides.get("processing_mode", "") or "")
        if hasattr(request, "audio_source"):
            request.audio_source = str(overrides.get("audio_source", "") or "")
        if hasattr(request, "audio_file_path"):
            request.audio_file_path = str(overrides.get("audio_file_path", "") or "")
        if hasattr(request, "language"):
            request.language = str(overrides.get("language", "") or "")
        if hasattr(request, "mic_capture_sec"):
            request.mic_capture_sec = self._coerce_float(overrides.get("mic_capture_sec", 0.0))
        if hasattr(request, "runtime_namespace") and runtime_namespace:
            request.runtime_namespace = runtime_namespace
        if auto_start_audio is not None and hasattr(request, "auto_start_audio"):
            request.auto_start_audio = bool(auto_start_audio)

    def _configure_runtime_stage(
        self,
        service_name: str,
        *,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
        overrides: dict[str, object],
    ) -> str:
        request = ReconfigureRuntime.Request()
        self._populate_runtime_stage_request(
            request,
            session_id=session_id,
            runtime_profile=runtime_profile,
            provider_profile=provider_profile,
            overrides=overrides,
        )
        response = self._call_service(ReconfigureRuntime, service_name, request)
        if not response.success:
            raise RuntimeError(response.message)
        return response.resolved_config_ref

    def _reconfigure_runtime_nodes(
        self,
        request,
        overrides: dict[str, object],
        *,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
    ) -> str:
        # Fan configuration changes out to the other runtime stages first, then
        # keep the latest resolved snapshot path for observability/debugging.
        del request
        resolved_ref = ""
        for service_name in (
            "/asr/runtime/preprocess/reconfigure",
            "/asr/runtime/vad/reconfigure",
            "/asr/runtime/audio/reconfigure",
        ):
            stage_ref = self._configure_runtime_stage(
                service_name,
                session_id=session_id,
                runtime_profile=runtime_profile,
                provider_profile=provider_profile,
                overrides=overrides,
            )
            resolved_ref = stage_ref or resolved_ref
        return resolved_ref

    def _start_audio_session(
        self,
        request,
        overrides: dict[str, object],
        *,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
    ) -> None:
        audio_request = StartRuntimeSession.Request()
        self._populate_runtime_stage_request(
            audio_request,
            session_id=session_id,
            runtime_profile=runtime_profile,
            provider_profile=provider_profile,
            overrides=overrides,
            runtime_namespace=request.runtime_namespace,
            auto_start_audio=True,
        )
        audio_res = self._call_service(
            StartRuntimeSession,
            "/asr/runtime/audio/start_session",
            audio_request,
            timeout_sec=10.0,
        )
        if not audio_res.accepted:
            raise RuntimeError(audio_res.message)

    def _stop_audio_session(self, session_id: str) -> None:
        request = StopRuntimeSession.Request()
        request.session_id = session_id
        response = self._call_service(
            StopRuntimeSession,
            "/asr/runtime/audio/stop_session",
            request,
            timeout_sec=10.0,
        )
        if not response.success:
            raise RuntimeError(response.message)

    def _activate_session(self, session_id: str) -> None:
        now = self.get_clock().now()
        self.session_id = session_id
        self.session_state = "ready"
        self.audio_session_active = False
        self._stream_active = False
        self._stream_request_id = ""
        self._stop_requested_at = None
        self.session_started_at = now
        self.session_updated_at = now
        self.session_ended_at = None
        self.last_error_code = ""
        self.last_error_message = ""

    def _read_recognize_audio_bytes(self, wav_path: str) -> bytes:
        if not wav_path:
            return b""
        path = Path(wav_path)
        if not path.exists():
            raise FileNotFoundError(f"WAV file not found: {wav_path}")
        return path.read_bytes()

    def _export_runtime_trace(self, trace) -> str:
        if self._trace_exporter is None:
            return ""
        try:
            return self._trace_exporter.export_runtime_trace(trace)
        except Exception as exc:
            self.get_logger().warning(f"Runtime trace export failed: {exc}")
            return ""

    def _resolve_recognize_provider(
        self,
        *,
        provider_profile: str,
        provider_preset: str,
        provider_settings: dict[str, object],
    ):
        current_provider = AsrOrchestratorNode._active_provider(self)
        resolved_profile = self._choose_requested_value(
            provider_profile,
            self.provider_profile,
        )
        if (
            resolved_profile == self.provider_profile
            and not provider_preset
            and not provider_settings
        ):
            return current_provider, False, self.provider_profile
        provider = self.provider_manager.create_from_profile(
            resolved_profile,
            preset_id=provider_preset,
            settings_overrides=dict(provider_settings),
        )
        return provider, True, resolved_profile

    def _on_segment(self, msg: AudioSegment) -> None:
        # Segmented mode is the simpler mental model:
        # VAD cuts one utterance -> provider recognizes one utterance.
        if self.processing_mode != "segmented":
            return
        if msg.session_id != self.session_id:
            return
        if self.provider is None or self.session_state not in {
            "ready",
            "running",
            "stopping",
            "degraded",
        }:
            return

        was_stopping = self.session_state == "stopping"
        self.session_state = "running"
        self.session_updated_at = self.get_clock().now()
        request_id = make_request_id()
        audio = ProviderAudio(
            session_id=msg.session_id or self.session_id,
            request_id=request_id,
            language=self.language,
            sample_rate_hz=int(msg.sample_rate),
            audio_bytes=bytes(msg.data),
            enable_word_timestamps=True,
            metadata={
                "segment_id": str(getattr(msg, "segment_id", "") or ""),
                "source_id": str(getattr(msg, "source_id", "") or ""),
                "metadata_ref": str(getattr(msg, "metadata_ref", "") or ""),
                "channels": int(msg.channels or 1),
                "encoding": str(msg.encoding or "pcm_s16le"),
                "sample_width_bytes": sample_width_from_encoding(msg.encoding, default=2),
            },
        )
        try:
            result = self.provider.recognize_once(audio)
            self._publish_result(result)
            if was_stopping:
                self.session_state = "stopped"
                self.session_ended_at = self.get_clock().now()
                self.session_updated_at = self.session_ended_at
                self._stop_requested_at = None
            else:
                # Keep the session receptive to subsequent segments even when one
                # segment yields a degraded/empty result.
                self.session_state = "ready"
        except Exception as exc:
            self._handle_provider_runtime_failure(
                error_code="provider_segment_error",
                error_message=str(exc),
                request_id=request_id,
            )

    def _publish_partial_result(self, result: NormalizedAsrResult) -> None:
        partial_msg = to_partial_msg(result)
        partial_msg.header.stamp = self.get_clock().now().to_msg()
        self.partial_pub.publish(partial_msg)
        self.session_updated_at = self.get_clock().now()

    @staticmethod
    def _log_excerpt(value: object, *, limit: int = 160) -> str:
        text = " ".join(str(value or "").split())
        if len(text) <= limit:
            return text
        return f"{text[: limit - 3]}..."

    def _publish_result(self, result: NormalizedAsrResult) -> None:
        final_msg = to_asr_result_msg(result)
        final_msg.header.stamp = self.get_clock().now().to_msg()
        self.final_pub.publish(final_msg)

        self.last_error_code = result.error_code
        self.last_error_message = result.error_message
        self.session_updated_at = self.get_clock().now()

        log_line = (
            "Final ASR result published: "
            f"session={result.session_id or self.session_id} "
            f"request={result.request_id} "
            f"provider={result.provider_id or self.provider_id or 'unknown'} "
            f"success={not bool(result.error_code)} "
            f"degraded={bool(result.degraded)} "
            f"latency_ms={float(result.latency.total_ms):.1f} "
            f"text={json.dumps(self._log_excerpt(result.text), ensure_ascii=True)}"
        )
        error_excerpt = self._log_excerpt(result.error_message, limit=200)
        if error_excerpt:
            log_line = (
                f"{log_line} error_code={result.error_code or 'none'} "
                f"error_message={json.dumps(error_excerpt, ensure_ascii=True)}"
            )
        if result.error_code or result.degraded:
            self.get_logger().warning(log_line)
        else:
            self.get_logger().info(log_line)

    def _handle_stream_update(self, result: NormalizedAsrResult | None) -> None:
        if result is None:
            return
        if result.is_partial:
            if self.enable_partials and result.text:
                self._publish_partial_result(result)
            return
        self._publish_result(result)

    def _publish_runtime_error_result(
        self, *, request_id: str, error_code: str, error_message: str
    ) -> None:
        self._publish_result(
            NormalizedAsrResult(
                request_id=request_id or make_request_id(),
                session_id=self.session_id,
                provider_id=self.provider_id,
                text="",
                is_final=True,
                is_partial=False,
                language=self.language,
                latency=LatencyMetadata(total_ms=0.0),
                degraded=True,
                error_code=error_code,
                error_message=error_message,
            )
        )

    def _handle_provider_runtime_failure(
        self, *, error_code: str, error_message: str, request_id: str = ""
    ) -> None:
        now = self.get_clock().now()
        self.last_error_code = error_code
        self.last_error_message = error_message
        self.session_state = "error"
        self.audio_session_active = False
        self.session_ended_at = now
        self.session_updated_at = now
        self._stream_active = False
        self._stream_request_id = ""
        self._stop_requested_at = None

        try:
            self._publish_runtime_error_result(
                request_id=request_id or self._stream_request_id or make_request_id(),
                error_code=error_code,
                error_message=error_message,
            )
        except Exception as exc:
            self.last_error_message = (
                f"{self.last_error_message}; error_result_publish_failed: {exc}"
            )

        try:
            if self.provider is not None:
                self.provider.teardown()
        except Exception as exc:
            self.last_error_message = f"{self.last_error_message}; provider_teardown_failed: {exc}"

        try:
            self._stop_audio_session(self.session_id)
        except Exception as exc:
            self.last_error_message = f"{self.last_error_message}; audio_stop_failed: {exc}"

    def _should_accept_stream_chunk(self, msg: AudioChunk) -> bool:
        if self.processing_mode != "provider_stream":
            return False
        if msg.session_id != self.session_id:
            return False
        if self.provider is None or self.session_state not in {
            "ready",
            "running",
            "stopping",
            "degraded",
        }:
            return False
        return bool(self.provider.discover_capabilities().supports_streaming)

    def _stream_start_options(self, msg: AudioChunk) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "request_id": self._stream_request_id,
            "language": self.language,
            "sample_rate_hz": int(msg.sample_rate or 16000),
            "channels": int(msg.channels or 1),
            "encoding": str(msg.encoding or "pcm_s16le"),
            "sample_width_bytes": int(sample_width_from_encoding(msg.encoding, default=2)),
        }

    def _ensure_provider_stream_started(self, msg: AudioChunk) -> None:
        if self._stream_active:
            return
        self._stream_request_id = make_request_id()
        AsrOrchestratorNode._active_provider(self).start_stream(
            self._stream_start_options(msg)
        )
        self._stream_active = True

    def _forward_stream_audio(self, msg: AudioChunk) -> None:
        if not msg.data:
            return
        provider = AsrOrchestratorNode._active_provider(self)
        partial = provider.push_audio(bytes(msg.data))
        self._handle_stream_update(partial)
        for pending in provider.drain_stream_results():
            self._handle_stream_update(pending)

    def _finish_provider_stream(self) -> None:
        provider = AsrOrchestratorNode._active_provider(self)
        result = provider.stop_stream()
        for pending in provider.drain_stream_results():
            self._handle_stream_update(pending)
        self._stream_active = False
        self._publish_result(result)
        self.audio_session_active = False
        self.session_state = "stopped"
        self.session_ended_at = self.get_clock().now()
        self.session_updated_at = self.session_ended_at
        self._stop_requested_at = None

    def _on_preprocessed_chunk(self, msg: AudioChunk) -> None:
        # Provider-stream mode forwards chunks directly to a streaming-capable
        # backend and publishes partial/final updates as they arrive.
        if not self._should_accept_stream_chunk(msg):
            return
        try:
            self._ensure_provider_stream_started(msg)
            was_stopping = self.session_state == "stopping"
            self.session_state = "running"
            self.session_updated_at = self.get_clock().now()
            self._forward_stream_audio(msg)
            if msg.is_last_chunk or was_stopping:
                self._finish_provider_stream()
        except Exception as exc:
            self._handle_provider_runtime_failure(
                error_code="provider_stream_error",
                error_message=str(exc),
                request_id=self._stream_request_id,
            )

    @staticmethod
    def _copy_result_message(source: AsrResult, target: AsrResult) -> None:
        target.header = source.header
        target.request_id = source.request_id
        target.text = source.text
        target.partials = list(source.partials)
        target.confidence = float(source.confidence)
        target.word_timestamps = list(source.word_timestamps)
        target.language = source.language
        target.backend = source.backend
        target.model = source.model
        target.region = source.region
        target.audio_duration_sec = float(source.audio_duration_sec)
        target.preprocess_ms = float(source.preprocess_ms)
        target.inference_ms = float(source.inference_ms)
        target.postprocess_ms = float(source.postprocess_ms)
        target.total_ms = float(source.total_ms)
        target.is_final = bool(source.is_final)
        target.success = bool(source.success)
        target.error_code = source.error_code
        target.error_message = source.error_message
        target.session_id = source.session_id
        target.provider_id = source.provider_id
        target.is_partial = bool(source.is_partial)
        target.confidence_available = bool(source.confidence_available)
        target.timestamps_available = bool(source.timestamps_available)
        target.utterance_start = source.utterance_start
        target.utterance_end = source.utterance_end
        target.first_partial_latency_ms = float(source.first_partial_latency_ms)
        target.finalization_latency_ms = float(source.finalization_latency_ms)
        target.raw_metadata_ref = source.raw_metadata_ref
        target.degraded = bool(source.degraded)
        target.tags = list(source.tags)

    def _on_start_session(
        self, request: StartRuntimeSession.Request, response: StartRuntimeSession.Response
    ):
        # Starting a session touches provider setup, sibling runtime nodes, and
        # internal session state. Keep a full rollback snapshot so a failure in
        # the middle does not leave the runtime half-reconfigured.
        snapshot = self._snapshot_runtime_state()
        target_runtime_profile = self._choose_requested_value(
            request.runtime_profile,
            self.runtime_profile,
        )
        target_provider_profile = self._choose_requested_value(
            request.provider_profile,
            self.provider_profile,
        )
        target_session_id = self._choose_requested_value(
            request.session_id,
            "",
            default=make_session_id(),
        )

        if request.auto_start_audio and self.audio_session_active:
            response.accepted = False
            response.session_id = self.session_id
            response.message = f"Runtime session already active: {self.session_id}"
            return response

        try:
            overrides = self._build_overrides_from_request(request)
            resolved_ref = self._load_runtime_configuration(
                overrides,
                runtime_profile=target_runtime_profile,
                provider_profile=target_provider_profile,
            )
            resolved_ref = (
                self._reconfigure_runtime_nodes(
                    request,
                    overrides,
                    session_id=target_session_id,
                    runtime_profile=self.runtime_profile,
                    provider_profile=self.provider_profile,
                )
                or resolved_ref
            )

            self._activate_session(target_session_id)

            if request.auto_start_audio:
                self._start_audio_session(
                    request,
                    overrides,
                    session_id=target_session_id,
                    runtime_profile=self.runtime_profile,
                    provider_profile=self.provider_profile,
                )

            self.session_state = "running" if request.auto_start_audio else "ready"
            self.audio_session_active = bool(request.auto_start_audio)
            response.accepted = True
            response.session_id = self.session_id
            response.message = "Runtime session started"
            response.resolved_config_ref = resolved_ref
        except Exception as exc:
            if self.provider is not None and self.provider is not snapshot.provider:
                self.provider.teardown()
            self._restore_runtime_state(snapshot)
            response.accepted = False
            response.session_id = target_session_id
            response.message = str(exc)
            self.last_error_code = "runtime_start_failed"
            self.last_error_message = str(exc)
            self.session_state = "error"
        return response

    def _on_stop_session(
        self, request: StopRuntimeSession.Request, response: StopRuntimeSession.Response
    ):
        requested_session_id = str(request.session_id).strip()
        if (
            requested_session_id
            and requested_session_id.lower() not in {"none", "null"}
            and requested_session_id != self.session_id
        ):
            response.success = False
            response.message = "Session ID mismatch"
            return response
        stop_session_id = (
            requested_session_id
            if requested_session_id and requested_session_id.lower() not in {"none", "null"}
            else ""
        )

        try:
            self._stop_audio_session(stop_session_id)
        except Exception as exc:
            self.last_error_code = "runtime_stop_failed"
            self.last_error_message = str(exc)
            response.success = False
            response.message = str(exc)
            return response

        if stop_session_id:
            self.session_id = stop_session_id
        self.audio_session_active = False
        self.session_state = "stopping"
        self._stop_requested_at = self.get_clock().now()
        self.session_updated_at = self._stop_requested_at
        self.last_error_code = ""
        self.last_error_message = ""
        if self.processing_mode == "provider_stream" and not self._stream_active:
            self.session_state = "stopped"
            self.session_ended_at = self._stop_requested_at
            self.audio_session_active = False
            self._stop_requested_at = None
        response.success = True
        response.message = "Runtime session stopped"
        return response

    def _on_reconfigure(
        self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response
    ):
        try:
            # Reconfiguring a live provider stream mid-flight is risky because
            # provider-side stream state may become inconsistent.
            if self.audio_session_active and self.processing_mode == "provider_stream":
                raise RuntimeError("Cannot reconfigure runtime while provider stream is active")
            requested_runtime_profile = str(request.runtime_profile).strip()
            requested_provider_profile = str(request.provider_profile).strip()

            target_runtime_profile = self._choose_requested_value(
                requested_runtime_profile,
                self.runtime_profile,
            )
            target_provider_profile = self._choose_requested_value(
                requested_provider_profile,
                self.provider_profile,
            )

            overrides = self._build_overrides_from_request(request)
            resolved_ref = self._load_runtime_configuration(
                overrides,
                runtime_profile=target_runtime_profile,
                provider_profile=target_provider_profile,
            )
            resolved_ref = (
                self._reconfigure_runtime_nodes(
                    request,
                    overrides,
                    session_id=self.session_id,
                    runtime_profile=self.runtime_profile,
                    provider_profile=self.provider_profile,
                )
                or resolved_ref
            )
            self.session_updated_at = self.get_clock().now()
            self.last_error_code = ""
            self.last_error_message = ""
            response.success = True
            response.message = "Runtime reconfigured"
            response.resolved_config_ref = resolved_ref
        except Exception as exc:
            self.last_error_code = "runtime_reconfigure_failed"
            self.last_error_message = str(exc)
            response.success = False
            response.message = str(exc)
            response.resolved_config_ref = ""
        return response

    def _on_recognize_once(self, request: RecognizeOnce.Request, response: RecognizeOnce.Response):
        # Recognize-once is the "direct test" path: transcribe one WAV without
        # needing VAD/session startup, while still reusing provider profile logic.
        if self.provider is None:
            response.result.success = False
            response.result.error_message = "Provider is not initialized"
            return response
        collector = PipelineTraceCollector(
            trace_type="runtime_recognize_once",
            request_id="",
            session_id=str(request.session_id or self.session_id or ""),
            provider_id=str(getattr(self, "provider_id", "") or ""),
            metadata={
                "runtime_profile": str(getattr(self, "runtime_profile", "") or ""),
                "provider_profile": str(getattr(self, "provider_profile", "") or ""),
                "api": "/asr/runtime/recognize_once",
            },
        )
        wav_path = str(request.wav_path).strip()
        audio_duration_sec = 0.0
        try:
            with collector.stage(
                "audio_load",
                component=(
                    self.get_name()
                    if callable(getattr(self, "get_name", None))
                    else "asr_orchestrator_node"
                ),
                code_path="asr_runtime_nodes.asr_orchestrator_node._on_recognize_once",
                input_summary={"wav_path": wav_path},
            ) as stage_output:
                audio_bytes = self._read_recognize_audio_bytes(wav_path)
                if wav_path:
                    try:
                        audio_duration_sec = float(wav_duration_sec(wav_path))
                    except Exception:
                        audio_duration_sec = 0.0
                stage_output["bytes_read"] = len(audio_bytes)
                stage_output["audio_duration_sec"] = audio_duration_sec
        except FileNotFoundError as exc:
            response.result.success = False
            response.result.error_message = str(exc)
            return response

        clean_session_id = self._choose_requested_value(
            request.session_id,
            self.session_id,
        )
        clean_language = self._choose_requested_value(
            request.language,
            self.language,
        )
        clean_provider_profile = self._choose_requested_value(
            getattr(request, "provider_profile", ""),
            self.provider_profile,
        )
        try:
            overrides = self._build_overrides_from_request(request)
        except Exception as exc:
            response.result.success = False
            response.result.error_message = str(exc)
            return response

        try:
            active_provider, should_teardown_provider, resolved_profile = (
                self._resolve_recognize_provider(
                    provider_profile=clean_provider_profile,
                    provider_preset=str(overrides.get("provider_preset", "") or ""),
                    provider_settings=dict(overrides.get("provider_settings", {}) or {}),
                )
            )
        except Exception as exc:
            response.result.success = False
            response.result.error_message = str(exc)
            response.resolved_profile = clean_provider_profile
            return response

        req = ProviderAudio(
            session_id=clean_session_id,
            request_id=make_request_id(),
            language=clean_language,
            sample_rate_hz=16000,
            wav_path=wav_path,
            audio_bytes=audio_bytes,
            enable_word_timestamps=bool(request.enable_word_timestamps),
        )
        collector.trace.request_id = req.request_id
        collector.trace.session_id = clean_session_id
        collector.update_metadata(
            resolved_profile=resolved_profile,
            requested_language=clean_language,
            wav_path=wav_path,
        )
        try:
            try:
                with collector.stage(
                    "provider_recognize",
                    component=(
                        getattr(active_provider, "provider_id", "")
                        or str(getattr(self, "provider_id", "") or "provider")
                    ),
                    code_path=(
                        f"{type(active_provider).__module__}."
                        f"{type(active_provider).__name__}.recognize_once"
                    ),
                    input_summary={
                        "audio_duration_sec": audio_duration_sec,
                        "enable_word_timestamps": bool(request.enable_word_timestamps),
                    },
                ) as stage_output:
                    result = active_provider.recognize_once(req)
                    stage_output["provider_id"] = result.provider_id
                    stage_output["success"] = not bool(result.error_code)
                    stage_output["text_length"] = len(str(result.text or ""))
                    stage_output["latency_ms"] = float(result.latency.total_ms)
            except Exception as exc:
                self.last_error_code = "recognize_once_failed"
                self.last_error_message = str(exc)
                self.session_updated_at = self.get_clock().now()
                response.result.success = False
                response.result.error_code = self.last_error_code
                response.result.error_message = self.last_error_message
                response.resolved_profile = resolved_profile
                return response

            if getattr(self, "_observability_config", None) is not None:
                trace = build_runtime_trace(
                    collector=collector,
                    config=self._observability_config,
                    provider_id=result.provider_id or getattr(active_provider, "provider_id", ""),
                    text=result.text,
                    confidence=result.confidence,
                    success=not result.degraded and not result.error_code,
                    degraded=result.degraded,
                    error_code=result.error_code,
                    error_message=result.error_message,
                    language=result.language or clean_language,
                    audio_duration_sec=audio_duration_sec,
                    preprocess_ms=float(result.latency.preprocess_ms),
                    inference_ms=float(result.latency.inference_ms),
                    postprocess_ms=float(result.latency.postprocess_ms),
                    total_latency_ms=float(result.latency.total_ms),
                )
                if trace.validation.corrupted:
                    result.tags.append("metrics_corrupted")
                    self.get_logger().warning(
                        "Runtime trace validation failed for request "
                        f"{req.request_id}: {'; '.join(trace.validation.errors)}"
                    )
                trace_path = self._export_runtime_trace(trace)
                if trace_path:
                    result.raw_metadata_ref = trace_path

            self._copy_result_message(to_asr_result_msg(result), response.result)
            response.resolved_profile = resolved_profile
            self._publish_result(result)
        finally:
            if should_teardown_provider and active_provider is not None:
                active_provider.teardown()
        return response

    def _on_list_profiles(self, request: ListProfiles.Request, response: ListProfiles.Response):
        response.profile_ids = list_profiles(
            request.profile_type or "runtime", configs_root=self.configs_root
        )
        return response

    def _on_list_backends(self, request: ListBackends.Request, response: ListBackends.Response):
        del request
        response.provider_ids = list_providers()
        return response

    def _on_validate(self, request: ValidateConfig.Request, response: ValidateConfig.Response):
        try:
            profile_type = request.profile_type or "runtime"
            profile_id = request.profile_id
            if request.config_path:
                candidate = Path(request.config_path)
                if not candidate.exists():
                    raise FileNotFoundError(f"Config path not found: {candidate}")
            resolved = resolve_profile(
                profile_type=profile_type,
                profile_id=profile_id,
                configs_root=self.configs_root,
            )
            response.valid = True
            response.message = "valid"
            response.resolved_config_ref = resolved.snapshot_path
        except Exception as exc:
            response.valid = False
            response.message = str(exc)
            response.resolved_config_ref = ""
        return response

    def _on_get_status(self, request: GetAsrStatus.Request, response: GetAsrStatus.Response):
        del request
        response.backend = self.provider_id
        response.model = self.provider_preset
        response.region = ""
        response.cloud_credentials_available = self.provider is not None
        if self.provider is not None:
            caps = self.provider.discover_capabilities()
            response.capabilities = [
                f"streaming={caps.supports_streaming}",
                f"streaming_mode={caps.streaming_mode}",
                f"batch={caps.supports_batch}",
                f"word_timestamps={caps.supports_word_timestamps}",
                f"confidence={caps.supports_confidence}",
            ]
            response.streaming_supported = caps.supports_streaming
            response.streaming_mode = caps.streaming_mode
            if caps.requires_network:
                try:
                    response.cloud_credentials_available = len(self.provider.validate_config()) == 0
                except Exception:
                    response.cloud_credentials_available = False
        response.status_message = self.session_state
        response.session_id = self.session_id
        response.session_state = self.session_state
        response.processing_mode = self.processing_mode
        response.audio_source = self.audio_source
        response.runtime_profile = self.runtime_profile
        return response

    def _publish_status(self) -> None:
        now = self.get_clock().now()
        if self.session_state == "stopping" and self._stop_requested_at is not None:
            elapsed_ns = now.nanoseconds - self._stop_requested_at.nanoseconds
            if elapsed_ns >= 1_500_000_000:
                self.session_state = "stopped"
                self.session_ended_at = now
                self.session_updated_at = now
                self._stop_requested_at = None

        node_status = NodeStatus()
        node_status.header.stamp = now.to_msg()
        node_status.node_name = self.get_name()
        node_status.lifecycle_state = "active"
        node_status.health = "ok" if not self.last_error_code else "degraded"
        node_status.status_message = (
            f"{self.session_state} provider={self.provider_id or 'n/a'} "
            f"preset={self.provider_preset or 'default'} "
            f"mode={self.processing_mode} source={self.audio_source}"
        )
        node_status.ready = self.session_state in {"ready", "running", "stopped"}
        node_status.last_error_code = self.last_error_code
        node_status.last_error_message = self.last_error_message
        node_status.last_update = now.to_msg()
        self.node_status_pub.publish(node_status)

        session_status = SessionStatus()
        session_status.header.stamp = now.to_msg()
        session_status.session_id = self.session_id
        session_status.state = self.session_state
        session_status.provider_id = self.provider_id
        session_status.profile_id = self.runtime_profile
        session_status.processing_mode = self.processing_mode
        session_status.started_at = self.session_started_at.to_msg()
        session_status.updated_at = self.session_updated_at.to_msg()
        if self.session_ended_at is not None:
            session_status.ended_at = self.session_ended_at.to_msg()
        session_status.status_message = (
            f"{self.session_state} source={self.audio_source} "
            f"mode={self.processing_mode} preset={self.provider_preset or 'default'}"
        )
        session_status.error_code = self.last_error_code
        session_status.error_message = self.last_error_message
        self.session_status_pub.publish(session_status)


def main() -> None:
    rclpy.init()
    node = AsrOrchestratorNode()
    try:
        spin_node_until_shutdown(node=node, rclpy_module=rclpy)
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
