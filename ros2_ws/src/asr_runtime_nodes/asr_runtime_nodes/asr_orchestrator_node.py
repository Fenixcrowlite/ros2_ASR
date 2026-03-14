"""ASR orchestrator node selecting provider adapters and coordinating runtime pipeline."""

from __future__ import annotations

import uuid
from pathlib import Path

import rclpy
from asr_config import list_profiles, resolve_profile, validate_runtime_payload
from asr_core import TOPICS, make_request_id, make_session_id
from asr_core.audio import sample_width_from_encoding
from asr_core.normalized import NormalizedAsrResult
from asr_core.shutdown import safe_shutdown_node
from asr_interfaces.msg import AsrResult, AsrResultPartial, AudioSegment, NodeStatus, SessionStatus
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
from asr_runtime_nodes.converters import to_asr_result_msg
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


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

        self.provider_manager = ProviderManager(configs_root=self.configs_root)
        self.provider = None
        self.provider_id = ""
        self.language = "en-US"
        self.enable_partials = True
        self.audio_source = "file"
        self.max_concurrent_sessions = 1
        self._load_runtime_configuration(overrides={})

        self.final_pub = self.create_publisher(AsrResult, TOPICS["final_results"], 10)
        self.partial_pub = self.create_publisher(AsrResultPartial, TOPICS["partial_results"], 10)
        self.node_status_pub = self.create_publisher(NodeStatus, TOPICS["node_status"], 10)
        self.session_status_pub = self.create_publisher(SessionStatus, TOPICS["session_status"], 10)

        self.segment_sub = self.create_subscription(
            AudioSegment,
            TOPICS["speech_segments"],
            self._on_segment,
            10,
        )

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
        self.status_srv = self.create_service(GetAsrStatus, "/asr/runtime/get_status", self._on_get_status)

        self.status_timer = self.create_timer(1.0, self._publish_status)
        self.session_state = "ready"

    def _build_overrides_from_request(self, request) -> dict[str, object]:
        return {
            "audio_source": str(getattr(request, "audio_source", "") or "").strip(),
            "audio_file_path": str(getattr(request, "audio_file_path", "") or "").strip(),
            "language": str(getattr(request, "language", "") or "").strip(),
            "mic_capture_sec": float(getattr(request, "mic_capture_sec", 0.0) or 0.0),
        }

    def _load_runtime_configuration(
        self,
        overrides: dict[str, object],
        *,
        runtime_profile: str | None = None,
        provider_profile: str | None = None,
    ) -> str:
        runtime_profile_id = str(runtime_profile or self.runtime_profile or "").strip()
        if runtime_profile_id.startswith("runtime/"):
            runtime_profile_id = runtime_profile_id.split("/", 1)[1]

        runtime_cfg = resolve_profile(
            profile_type="runtime",
            profile_id=runtime_profile_id,
            configs_root=self.configs_root,
        )
        errors = validate_runtime_payload(runtime_cfg.data)
        if errors:
            raise ValueError(f"Runtime profile validation failed: {'; '.join(errors)}")

        orchestrator_cfg = runtime_cfg.data.get("orchestrator", {})
        audio_cfg = runtime_cfg.data.get("audio", {})
        session_cfg = runtime_cfg.data.get("session", {})
        if not isinstance(orchestrator_cfg, dict):
            raise ValueError("runtime.orchestrator must be an object")
        if not isinstance(audio_cfg, dict):
            raise ValueError("runtime.audio must be an object")
        if not isinstance(session_cfg, dict):
            raise ValueError("runtime.session must be an object")

        target_provider_profile = str(provider_profile or self.provider_profile or "").strip() or str(
            orchestrator_cfg.get("provider_profile", "providers/whisper_local")
        )
        requested_language = str(overrides.get("language", "") or "").strip()
        requested_audio_source = str(overrides.get("audio_source", "") or "").strip()
        target_language = requested_language or str(orchestrator_cfg.get("language", "en-US"))
        target_enable_partials = bool(orchestrator_cfg.get("enable_partials", True))
        target_audio_source = requested_audio_source or str(audio_cfg.get("source", "file"))
        target_max_concurrent_sessions = int(session_cfg.get("max_concurrent_sessions", 1) or 1)
        next_provider = self.provider_manager.create_from_profile(target_provider_profile)
        previous_provider = self.provider

        self.runtime_profile = runtime_profile_id
        self.provider_profile = target_provider_profile
        self.language = target_language
        self.enable_partials = target_enable_partials
        self.audio_source = target_audio_source
        self.max_concurrent_sessions = target_max_concurrent_sessions
        self.provider = next_provider
        self.provider_id = next_provider.provider_id
        if previous_provider is not None and previous_provider is not next_provider:
            previous_provider.teardown()
        return runtime_cfg.snapshot_path

    def _call_service(self, service_type, service_name: str, request, timeout_sec: float = 5.0):
        temp_node = Node(f"asr_orchestrator_client_{uuid.uuid4().hex[:8]}", use_global_arguments=False)
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

    def _reconfigure_runtime_nodes(
        self,
        request,
        overrides: dict[str, object],
        *,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
    ) -> str:
        resolved_ref = ""

        preprocess_request = ReconfigureRuntime.Request()
        preprocess_request.session_id = session_id
        preprocess_request.runtime_profile = runtime_profile
        preprocess_request.provider_profile = provider_profile
        preprocess_res = self._call_service(
            ReconfigureRuntime,
            "/asr/runtime/preprocess/reconfigure",
            preprocess_request,
        )
        if not preprocess_res.success:
            raise RuntimeError(preprocess_res.message)
        resolved_ref = preprocess_res.resolved_config_ref

        vad_request = ReconfigureRuntime.Request()
        vad_request.session_id = session_id
        vad_request.runtime_profile = runtime_profile
        vad_request.provider_profile = provider_profile
        vad_res = self._call_service(
            ReconfigureRuntime,
            "/asr/runtime/vad/reconfigure",
            vad_request,
        )
        if not vad_res.success:
            raise RuntimeError(vad_res.message)
        resolved_ref = vad_res.resolved_config_ref or resolved_ref

        audio_request = ReconfigureRuntime.Request()
        audio_request.session_id = session_id
        audio_request.runtime_profile = runtime_profile
        audio_request.provider_profile = provider_profile
        audio_request.audio_source = str(overrides.get("audio_source", "") or "")
        audio_request.audio_file_path = str(overrides.get("audio_file_path", "") or "")
        audio_request.language = str(overrides.get("language", "") or "")
        audio_request.mic_capture_sec = float(overrides.get("mic_capture_sec", 0.0) or 0.0)
        audio_res = self._call_service(
            ReconfigureRuntime,
            "/asr/runtime/audio/reconfigure",
            audio_request,
        )
        if not audio_res.success:
            raise RuntimeError(audio_res.message)
        return audio_res.resolved_config_ref or resolved_ref

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
        audio_request.runtime_profile = runtime_profile
        audio_request.provider_profile = provider_profile
        audio_request.session_id = session_id
        audio_request.runtime_namespace = request.runtime_namespace
        audio_request.auto_start_audio = True
        audio_request.audio_source = str(overrides.get("audio_source", "") or "")
        audio_request.audio_file_path = str(overrides.get("audio_file_path", "") or "")
        audio_request.language = str(overrides.get("language", "") or "")
        audio_request.mic_capture_sec = float(overrides.get("mic_capture_sec", 0.0) or 0.0)
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

    def _on_segment(self, msg: AudioSegment) -> None:
        if msg.session_id != self.session_id:
            return
        if self.provider is None or self.session_state not in {"ready", "running", "stopping", "degraded"}:
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
                "segment_id": str(msg.segment_id),
                "source_id": str(msg.source_id),
                "metadata_ref": str(msg.metadata_ref),
                "channels": int(msg.channels or 1),
                "encoding": str(msg.encoding or "pcm_s16le"),
                "sample_width_bytes": sample_width_from_encoding(msg.encoding, default=2),
            },
        )
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

    def _publish_result(self, result: NormalizedAsrResult) -> None:
        final_msg = to_asr_result_msg(result)
        final_msg.header.stamp = self.get_clock().now().to_msg()
        self.final_pub.publish(final_msg)

        self.last_error_code = result.error_code
        self.last_error_message = result.error_message
        self.session_updated_at = self.get_clock().now()

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

    def _on_start_session(self, request: StartRuntimeSession.Request, response: StartRuntimeSession.Response):
        previous_runtime_profile = self.runtime_profile
        previous_provider_profile = self.provider_profile
        previous_session_id = self.session_id
        previous_session_state = self.session_state
        previous_started_at = self.session_started_at
        previous_updated_at = self.session_updated_at
        previous_ended_at = self.session_ended_at
        previous_last_error_code = self.last_error_code
        previous_last_error_message = self.last_error_message
        previous_audio_source = self.audio_source
        previous_language = self.language
        previous_enable_partials = self.enable_partials
        previous_max_concurrent_sessions = self.max_concurrent_sessions
        previous_provider = self.provider
        previous_provider_id = self.provider_id
        previous_audio_session_active = self.audio_session_active

        requested_session_id = str(request.session_id).strip()
        requested_runtime_profile = str(request.runtime_profile).strip()
        requested_provider_profile = str(request.provider_profile).strip()
        overrides = self._build_overrides_from_request(request)
        target_runtime_profile = (
            requested_runtime_profile
            if requested_runtime_profile and requested_runtime_profile.lower() not in {"none", "null"}
            else self.runtime_profile
        )
        target_provider_profile = (
            requested_provider_profile
            if requested_provider_profile and requested_provider_profile.lower() not in {"none", "null"}
            else self.provider_profile
        )
        target_session_id = (
            requested_session_id
            if requested_session_id and requested_session_id.lower() not in {"none", "null"}
            else make_session_id()
        )

        if request.auto_start_audio and self.audio_session_active:
            response.accepted = False
            response.session_id = self.session_id
            response.message = f"Runtime session already active: {self.session_id}"
            return response

        try:
            resolved_ref = self._load_runtime_configuration(
                overrides,
                runtime_profile=target_runtime_profile,
                provider_profile=target_provider_profile,
            )
            resolved_ref = self._reconfigure_runtime_nodes(
                request,
                overrides,
                session_id=target_session_id,
                runtime_profile=self.runtime_profile,
                provider_profile=self.provider_profile,
            ) or resolved_ref

            provisional_started_at = self.get_clock().now()
            self.session_id = target_session_id
            self.session_state = "ready"
            self.audio_session_active = False
            self._stop_requested_at = None
            self.session_started_at = provisional_started_at
            self.session_updated_at = provisional_started_at
            self.session_ended_at = None
            self.last_error_code = ""
            self.last_error_message = ""

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
            self.runtime_profile = previous_runtime_profile
            self.provider_profile = previous_provider_profile
            self.session_id = previous_session_id
            self.session_state = previous_session_state
            self.session_started_at = previous_started_at
            self.session_updated_at = previous_updated_at
            self.session_ended_at = previous_ended_at
            self.audio_source = previous_audio_source
            self.language = previous_language
            self.enable_partials = previous_enable_partials
            self.max_concurrent_sessions = previous_max_concurrent_sessions
            self.audio_session_active = previous_audio_session_active
            if self.provider is not None and self.provider is not previous_provider:
                self.provider.teardown()
            self.provider = previous_provider
            self.provider_id = previous_provider_id
            self.last_error_code = previous_last_error_code
            self.last_error_message = previous_last_error_message
            response.accepted = False
            response.session_id = target_session_id
            response.message = str(exc)
            self.last_error_code = "runtime_start_failed"
            self.last_error_message = str(exc)
            self.session_state = "error"
        return response

    def _on_stop_session(self, request: StopRuntimeSession.Request, response: StopRuntimeSession.Response):
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
        response.success = True
        response.message = "Runtime session stopped"
        return response

    def _on_reconfigure(self, request: ReconfigureRuntime.Request, response: ReconfigureRuntime.Response):
        try:
            requested_runtime_profile = str(request.runtime_profile).strip()
            requested_provider_profile = str(request.provider_profile).strip()
            overrides = self._build_overrides_from_request(request)

            target_runtime_profile = (
                requested_runtime_profile
                if requested_runtime_profile and requested_runtime_profile.lower() not in {"none", "null"}
                else self.runtime_profile
            )
            target_provider_profile = (
                requested_provider_profile
                if requested_provider_profile and requested_provider_profile.lower() not in {"none", "null"}
                else self.provider_profile
            )

            resolved_ref = self._load_runtime_configuration(
                overrides,
                runtime_profile=target_runtime_profile,
                provider_profile=target_provider_profile,
            )
            resolved_ref = self._reconfigure_runtime_nodes(
                request,
                overrides,
                session_id=self.session_id,
                runtime_profile=self.runtime_profile,
                provider_profile=self.provider_profile,
            ) or resolved_ref
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
        if self.provider is None:
            response.result.success = False
            response.result.error_message = "Provider is not initialized"
            return response
        wav_path = str(request.wav_path).strip()
        audio_bytes = b""
        if wav_path:
            path = Path(wav_path)
            if not path.exists():
                response.result.success = False
                response.result.error_message = f"WAV file not found: {wav_path}"
                return response
            audio_bytes = path.read_bytes()

        requested_session_id = str(request.session_id).strip()
        clean_session_id = (
            requested_session_id
            if requested_session_id and requested_session_id.lower() not in {"none", "null"}
            else self.session_id
        )
        requested_language = str(request.language).strip()
        clean_language = (
            requested_language
            if requested_language and requested_language.lower() not in {"none", "null"}
            else self.language
        )

        req = ProviderAudio(
            session_id=clean_session_id,
            request_id=make_request_id(),
            language=clean_language,
            sample_rate_hz=16000,
            wav_path=wav_path,
            audio_bytes=audio_bytes,
            enable_word_timestamps=bool(request.enable_word_timestamps),
        )
        result = self.provider.recognize_once(req)
        self._copy_result_message(to_asr_result_msg(result), response.result)
        response.resolved_profile = self.provider_profile
        self._publish_result(result)
        return response

    def _on_list_profiles(self, request: ListProfiles.Request, response: ListProfiles.Response):
        response.profile_ids = list_profiles(request.profile_type or "runtime", configs_root=self.configs_root)
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
        response.model = ""
        response.region = ""
        if self.provider is not None:
            caps = self.provider.discover_capabilities()
            response.capabilities = [
                f"streaming={caps.supports_streaming}",
                f"batch={caps.supports_batch}",
                f"word_timestamps={caps.supports_word_timestamps}",
                f"confidence={caps.supports_confidence}",
            ]
            response.streaming_supported = caps.supports_streaming
            response.cloud_credentials_available = not caps.requires_network or True
        response.status_message = self.session_state
        response.session_id = self.session_id
        response.session_state = self.session_state
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
            f"{self.session_state} provider={self.provider_id or 'n/a'} source={self.audio_source}"
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
        session_status.started_at = self.session_started_at.to_msg()
        session_status.updated_at = self.session_updated_at.to_msg()
        if self.session_ended_at is not None:
            session_status.ended_at = self.session_ended_at.to_msg()
        session_status.status_message = f"{self.session_state} source={self.audio_source}"
        session_status.error_code = self.last_error_code
        session_status.error_message = self.last_error_message
        self.session_status_pub.publish(session_status)


def main() -> None:
    rclpy.init()
    node = AsrOrchestratorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
