"""ROS2 client facade for gateway operations."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import rclpy
from asr_core import TOPICS
from asr_interfaces.action import ImportDataset, RunBenchmarkExperiment
from asr_interfaces.msg import AsrResult, AsrResultPartial, NodeStatus, SessionStatus
from asr_interfaces.srv import (
    GetAsrStatus,
    GetBenchmarkStatus,
    ListBackends,
    ListDatasets,
    RecognizeOnce,
    ReconfigureRuntime,
    RegisterDataset,
    StartRuntimeSession,
    StopRuntimeSession,
    ValidateConfig,
)
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class GatewayResponse:
    # Tiny normalized envelope so the HTTP layer does not need to know ROS
    # response types for every service/action it calls.
    success: bool
    message: str
    payload: dict


def _stamp_to_iso(stamp: Any) -> str:
    sec = int(getattr(stamp, "sec", 0) or 0)
    nanosec = int(getattr(stamp, "nanosec", 0) or 0)
    if sec <= 0 and nanosec <= 0:
        return ""
    return datetime.fromtimestamp(sec + (nanosec / 1_000_000_000.0), tz=UTC).isoformat()


class RuntimeObserver:
    """Background ROS subscriber collecting live runtime signals for the gateway.

    The FastAPI app itself is request/response oriented, but the ASR runtime is
    topic-driven. This observer keeps a rolling snapshot of topic activity so
    web pages can ask for "current state" over HTTP.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._recent_results: deque[dict[str, Any]] = deque(maxlen=80)
        self._recent_partials: deque[dict[str, Any]] = deque(maxlen=80)
        self._node_statuses: dict[str, dict[str, Any]] = {}
        self._session_statuses: dict[str, dict[str, Any]] = {}
        self._started = False
        self._node: Node | None = None
        self._executor: SingleThreadedExecutor | None = None
        self._thread: threading.Thread | None = None
        self._error = ""

    def _record_error(self, context: str, exc: Exception) -> None:
        detail = f"{context}: {exc}"
        self._error = f"{self._error}; {detail}" if self._error else detail

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        try:
            # Run one long-lived observer node instead of creating new
            # subscriptions for every HTTP request.
            self._node = Node("asr_gateway_runtime_observer", use_global_arguments=False)
            retained_result_qos = QoSProfile(
                depth=10,
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
            )
            self._node.create_subscription(
                AsrResult,
                TOPICS["final_results"],
                self._on_final_result,
                retained_result_qos,
            )
            self._node.create_subscription(
                AsrResultPartial, TOPICS["partial_results"], self._on_partial_result, 10
            )
            self._node.create_subscription(
                NodeStatus, TOPICS["node_status"], self._on_node_status, 10
            )
            self._node.create_subscription(
                SessionStatus, TOPICS["session_status"], self._on_session_status, 10
            )
            self._executor = SingleThreadedExecutor()
            self._executor.add_node(self._node)
            self._thread = threading.Thread(
                target=self._spin, name="asr-gateway-runtime-observer", daemon=True
            )
            self._thread.start()
        except Exception as exc:
            self._record_error("observer_start_failed", exc)
            self._started = False
            try:
                if self._executor is not None:
                    self._executor.shutdown(timeout_sec=0.1)
            except Exception as cleanup_exc:
                self._record_error("observer_start_cleanup_failed", cleanup_exc)
            try:
                if self._node is not None:
                    self._node.destroy_node()
            except Exception as cleanup_exc:
                self._record_error("observer_start_cleanup_failed", cleanup_exc)
            self._executor = None
            self._node = None
            self._thread = None

    def _spin(self) -> None:
        if self._executor is None:
            return
        try:
            self._executor.spin()
        except Exception as exc:
            self._record_error("observer_spin_failed", exc)

    def stop(self) -> None:
        thread = self._thread
        try:
            if self._executor is not None:
                self._executor.shutdown(timeout_sec=0.5)
        except Exception as exc:
            self._record_error("observer_shutdown_failed", exc)
        try:
            if self._node is not None:
                self._node.destroy_node()
        except Exception as exc:
            self._record_error("observer_destroy_node_failed", exc)
        if thread is not None:
            try:
                thread.join(timeout=0.5)
                if thread.is_alive():
                    self._record_error(
                        "observer_join_failed", RuntimeError("observer thread did not stop")
                    )
            except Exception as exc:
                self._record_error("observer_join_failed", exc)
        self._started = False
        self._executor = None
        self._node = None
        self._thread = None

    def _push_unique(
        self,
        queue_ref: deque[dict[str, Any]],
        item: dict[str, Any],
        *,
        unique_key: str,
    ) -> None:
        # Latest message for a request_id should replace older copies so the UI
        # does not show the same result many times after repeated polling.
        unique_value = str(item.get(unique_key, "") or "").strip()
        if unique_value:
            deduped = [
                row
                for row in queue_ref
                if str(row.get(unique_key, "") or "").strip() != unique_value
            ]
            queue_ref.clear()
            queue_ref.extend(deduped[: queue_ref.maxlen or len(deduped)])
        queue_ref.appendleft(item)

    def _on_final_result(self, msg: AsrResult) -> None:
        payload = {
            "time": _stamp_to_iso(msg.header.stamp),
            "type": "final",
            "request_id": msg.request_id,
            "session_id": msg.session_id,
            "provider_id": msg.provider_id or msg.backend,
            "text": msg.text,
            "language": msg.language,
            "success": bool(msg.success),
            "error_code": msg.error_code,
            "error_message": msg.error_message,
            "latency_ms": float(msg.total_ms),
            "degraded": bool(msg.degraded),
            "raw_metadata_ref": msg.raw_metadata_ref,
        }
        with self._lock:
            self._push_unique(self._recent_results, payload, unique_key="request_id")

    def _on_partial_result(self, msg: AsrResultPartial) -> None:
        payload = {
            "time": _stamp_to_iso(msg.header.stamp),
            "type": "partial",
            "request_id": msg.request_id,
            "session_id": msg.session_id,
            "provider_id": msg.provider_id,
            "text": msg.text,
            "language": msg.language,
            "confidence": float(msg.confidence),
            "confidence_available": bool(msg.confidence_available),
            "latency_ms": float(msg.partial_latency_ms),
            "raw_metadata_ref": msg.raw_metadata_ref,
        }
        with self._lock:
            self._push_unique(self._recent_partials, payload, unique_key="request_id")

    def _on_node_status(self, msg: NodeStatus) -> None:
        payload = {
            "time": _stamp_to_iso(msg.header.stamp),
            "node_name": msg.node_name,
            "lifecycle_state": msg.lifecycle_state,
            "health": msg.health,
            "status_message": msg.status_message,
            "ready": bool(msg.ready),
            "last_error_code": msg.last_error_code,
            "last_error_message": msg.last_error_message,
            "last_update": _stamp_to_iso(msg.last_update),
        }
        with self._lock:
            self._node_statuses[msg.node_name] = payload

    def _on_session_status(self, msg: SessionStatus) -> None:
        payload = {
            "time": _stamp_to_iso(msg.header.stamp),
            "session_id": msg.session_id,
            "state": msg.state,
            "provider_id": msg.provider_id,
            "profile_id": msg.profile_id,
            "processing_mode": msg.processing_mode,
            "started_at": _stamp_to_iso(msg.started_at),
            "updated_at": _stamp_to_iso(msg.updated_at),
            "ended_at": _stamp_to_iso(msg.ended_at),
            "status_message": msg.status_message,
            "error_code": msg.error_code,
            "error_message": msg.error_message,
        }
        with self._lock:
            self._session_statuses[msg.session_id] = payload

    def record_result(self, payload: dict[str, Any]) -> None:
        request_id = str(payload.get("request_id", "") or "").strip()
        item = {
            "time": datetime.now(UTC).isoformat(),
            "type": str(payload.get("type", "final") or "final"),
            "request_id": request_id,
            "session_id": str(payload.get("session_id", "") or ""),
            "provider_id": str(payload.get("provider_id", "") or ""),
            "text": str(payload.get("text", "") or ""),
            "language": str(payload.get("language", "") or ""),
            "success": bool(payload.get("success", True)),
            "error_code": str(payload.get("error_code", "") or ""),
            "error_message": str(payload.get("error_message", "") or ""),
            "latency_ms": float(payload.get("latency_ms", 0.0) or 0.0),
            "degraded": bool(payload.get("degraded", False)),
            "raw_metadata_ref": str(payload.get("raw_metadata_ref", "") or ""),
        }
        with self._lock:
            self._push_unique(self._recent_results, item, unique_key="request_id")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            sessions = sorted(
                self._session_statuses.values(),
                key=lambda item: str(item.get("updated_at", "")),
                reverse=True,
            )
            return {
                "observer_error": self._error,
                "recent_results": list(self._recent_results),
                "recent_partials": list(self._recent_partials),
                "node_statuses": sorted(
                    self._node_statuses.values(), key=lambda item: item["node_name"]
                ),
                "session_statuses": sessions,
                "active_session": sessions[0] if sessions else {},
            }


class GatewayRosClient:
    """Synchronous helper around ROS services/actions for gateway endpoints.

    FastAPI handlers call into this class to translate plain Python payloads
    into ROS service/action requests and back into JSON-friendly dicts.
    """

    def __init__(self, timeout_sec: float = 5.0) -> None:
        self.timeout_sec = timeout_sec
        if not rclpy.ok():
            rclpy.init(args=None)
        self._observer = RuntimeObserver()
        self._observer.start()

    def close(self) -> None:
        self._observer.stop()

    def _node(self) -> Node:
        # Use short-lived client nodes so independent HTTP requests do not have
        # to share one mutable ROS client instance.
        return Node(f"asr_gateway_client_{uuid.uuid4().hex[:8]}", use_global_arguments=False)

    def _await_future(self, node: Node, future: Any, *, timeout_sec: float) -> bool:
        # Spin a private executor until the async ROS future finishes. This
        # keeps gateway code simple while still using ROS async clients safely.
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        try:
            deadline = datetime.now(UTC).timestamp() + timeout_sec
            while not future.done():
                remaining = deadline - datetime.now(UTC).timestamp()
                if remaining <= 0:
                    return False
                executor.spin_once(timeout_sec=min(0.2, remaining))
            return True
        finally:
            try:
                executor.shutdown(timeout_sec=0.1)
            except RuntimeError as exc:
                LOG.debug("executor shutdown during gateway client cleanup failed: %s", exc)

    def runtime_snapshot(self) -> dict[str, Any]:
        return self._observer.snapshot()

    def record_runtime_result(self, payload: dict[str, Any]) -> None:
        self._observer.record_result(payload)

    def _call_service(
        self,
        service_type: Any,
        service_name: str,
        *,
        request_builder: Callable[[Any], None],
        response_builder: Callable[[Any], GatewayResponse],
        unavailable_message: str,
        no_response_message: str,
        timeout_sec: float | None = None,
    ) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(service_type, service_name)
            effective_timeout = self.timeout_sec if timeout_sec is None else timeout_sec
            if not client.wait_for_service(timeout_sec=effective_timeout):
                return GatewayResponse(False, unavailable_message, {})
            request = service_type.Request()
            request_builder(request)
            future = client.call_async(request)
            if not self._await_future(node, future, timeout_sec=effective_timeout):
                return GatewayResponse(False, no_response_message, {})
            response = future.result()
            if response is None:
                return GatewayResponse(False, no_response_message, {})
            return response_builder(response)
        finally:
            node.destroy_node()

    def _call_action(
        self,
        action_type: Any,
        action_name: str,
        *,
        goal_builder: Callable[[Any], None],
        result_builder: Callable[[Any], GatewayResponse],
        unavailable_message: str,
        goal_timeout_message: str,
        goal_rejected_message: str,
        result_timeout_message: str,
        no_result_message: str,
        goal_timeout_sec: float | None = None,
        result_timeout_sec: float = 180.0,
    ) -> GatewayResponse:
        node = self._node()
        try:
            action = ActionClient(node, action_type, action_name)
            effective_goal_timeout = (
                self.timeout_sec if goal_timeout_sec is None else goal_timeout_sec
            )
            if not action.wait_for_server(timeout_sec=effective_goal_timeout):
                return GatewayResponse(False, unavailable_message, {})

            goal = action_type.Goal()
            goal_builder(goal)
            send_future = action.send_goal_async(goal)
            if not self._await_future(node, send_future, timeout_sec=effective_goal_timeout):
                return GatewayResponse(False, goal_timeout_message, {})
            goal_handle = send_future.result()
            if goal_handle is None or not goal_handle.accepted:
                return GatewayResponse(False, goal_rejected_message, {})

            result_future = goal_handle.get_result_async()
            if not self._await_future(node, result_future, timeout_sec=result_timeout_sec):
                return GatewayResponse(False, result_timeout_message, {})
            result = result_future.result()
            if result is None:
                return GatewayResponse(False, no_result_message, {})
            return result_builder(result)
        finally:
            node.destroy_node()

    def _populate_runtime_request(
        self,
        request: Any,
        *,
        runtime_profile: str,
        provider_profile: str,
        session_id: str,
        processing_mode: str,
        provider_preset: str,
        provider_settings: dict[str, Any] | None,
        audio_source: str,
        audio_file_path: str,
        language: str,
        mic_capture_sec: float,
    ) -> None:
        request.runtime_profile = runtime_profile
        request.provider_profile = provider_profile
        request.provider_preset = provider_preset
        request.provider_settings_json = json.dumps(provider_settings or {}, ensure_ascii=True)
        request.session_id = session_id
        request.processing_mode = processing_mode
        request.audio_source = audio_source
        request.audio_file_path = audio_file_path
        request.language = language
        request.mic_capture_sec = float(mic_capture_sec)

    def start_runtime(
        self,
        runtime_profile: str,
        provider_profile: str,
        session_id: str,
        *,
        processing_mode: str = "",
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
        audio_source: str = "",
        audio_file_path: str = "",
        language: str = "",
        mic_capture_sec: float = 0.0,
    ) -> GatewayResponse:
        # Mirrors the Runtime page "Start" action.
        def _build_request(request: Any) -> None:
            self._populate_runtime_request(
                request,
                runtime_profile=runtime_profile,
                provider_profile=provider_profile,
                session_id=session_id,
                processing_mode=processing_mode,
                provider_preset=provider_preset,
                provider_settings=provider_settings,
                audio_source=audio_source,
                audio_file_path=audio_file_path,
                language=language,
                mic_capture_sec=mic_capture_sec,
            )
            request.runtime_namespace = "/asr/runtime"
            request.auto_start_audio = True

        return self._call_service(
            StartRuntimeSession,
            "/asr/runtime/start_session",
            request_builder=_build_request,
            response_builder=lambda response: GatewayResponse(
                bool(response.accepted),
                response.message,
                {
                    "session_id": response.session_id,
                    "resolved": response.resolved_config_ref,
                },
            ),
            unavailable_message="start_session service unavailable",
            no_response_message="No response from start_session",
        )

    def stop_runtime(self, session_id: str) -> GatewayResponse:
        # Mirrors the Runtime page "Stop" action.
        return self._call_service(
            StopRuntimeSession,
            "/asr/runtime/stop_session",
            request_builder=lambda request: setattr(request, "session_id", session_id),
            response_builder=lambda response: GatewayResponse(
                bool(response.success),
                response.message,
                {},
            ),
            unavailable_message="stop_session service unavailable",
            no_response_message="No response from stop_session",
        )

    def reconfigure_runtime(
        self,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
        *,
        processing_mode: str = "",
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
        audio_source: str = "",
        audio_file_path: str = "",
        language: str = "",
        mic_capture_sec: float = 0.0,
    ) -> GatewayResponse:
        # Reconfigure keeps the session identity but pushes new config into the
        # runtime pipeline nodes.
        return self._call_service(
            ReconfigureRuntime,
            "/asr/runtime/reconfigure",
            request_builder=lambda request: self._populate_runtime_request(
                request,
                runtime_profile=runtime_profile,
                provider_profile=provider_profile,
                session_id=session_id,
                processing_mode=processing_mode,
                provider_preset=provider_preset,
                provider_settings=provider_settings,
                audio_source=audio_source,
                audio_file_path=audio_file_path,
                language=language,
                mic_capture_sec=mic_capture_sec,
            ),
            response_builder=lambda response: GatewayResponse(
                bool(response.success),
                response.message,
                {"resolved": response.resolved_config_ref},
            ),
            unavailable_message="reconfigure service unavailable",
            no_response_message="No response from reconfigure",
        )

    def recognize_once(
        self,
        wav_path: str,
        language: str,
        session_id: str,
        provider_profile: str,
        *,
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
    ) -> GatewayResponse:
        def _build_request(request: Any) -> None:
            request.wav_path = wav_path
            request.language = language
            request.enable_word_timestamps = True
            request.session_id = session_id
            request.provider_profile = provider_profile
            request.provider_preset = provider_preset
            request.provider_settings_json = json.dumps(provider_settings or {}, ensure_ascii=True)

        return self._call_service(
            RecognizeOnce,
            "/asr/runtime/recognize_once",
            request_builder=_build_request,
            response_builder=lambda response: GatewayResponse(
                bool(response.result.success),
                "ok",
                {
                    "request_id": response.result.request_id,
                    "session_id": response.result.session_id,
                    "text": response.result.text,
                    "provider_id": response.result.provider_id,
                    "success": bool(response.result.success),
                    "error_code": response.result.error_code,
                    "error_message": response.result.error_message,
                    "language": response.result.language,
                    "latency_ms": float(response.result.total_ms),
                    "degraded": bool(response.result.degraded),
                    "raw_metadata_ref": response.result.raw_metadata_ref,
                    "resolved_profile": response.resolved_profile,
                },
            ),
            unavailable_message="recognize_once service unavailable",
            no_response_message="No response from recognize_once",
            timeout_sec=max(self.timeout_sec, 20.0),
        )

    def run_benchmark(
        self,
        benchmark_profile: str,
        dataset_profile: str,
        providers: list[str],
        *,
        scenario: str = "",
        provider_overrides: dict[str, dict[str, Any]] | None = None,
        benchmark_settings: dict[str, Any] | None = None,
        run_id: str = "",
    ) -> GatewayResponse:
        def _build_goal(goal: Any) -> None:
            goal.benchmark_profile = benchmark_profile
            goal.dataset_profile = dataset_profile
            goal.run_id = run_id
            goal.providers = providers
            goal.scenario = scenario
            goal.provider_overrides_json = json.dumps(provider_overrides or {}, ensure_ascii=True)
            goal.benchmark_settings_json = json.dumps(benchmark_settings or {}, ensure_ascii=True)

        return self._call_action(
            RunBenchmarkExperiment,
            "/benchmark/run_experiment",
            goal_builder=_build_goal,
            result_builder=lambda result: GatewayResponse(
                bool(result.result.success),
                result.result.message,
                {
                    "run_id": result.result.run_id,
                    "success": bool(result.result.success),
                    "message": result.result.message,
                    "summary": {
                        "total_samples": int(result.result.summary.total_samples),
                        "successful_samples": int(result.result.summary.successful_samples),
                        "failed_samples": int(result.result.summary.failed_samples),
                        "mean_wer": float(result.result.summary.mean_wer),
                        "mean_cer": float(result.result.summary.mean_cer),
                        "mean_latency_ms": float(result.result.summary.mean_latency_ms),
                        "summary_artifact_ref": result.result.summary.summary_artifact_ref,
                    },
                },
            ),
            unavailable_message="benchmark action server unavailable",
            goal_timeout_message="Timed out waiting for benchmark goal response",
            goal_rejected_message="Benchmark goal not accepted",
            result_timeout_message="Timed out waiting for benchmark result",
            no_result_message="No benchmark result",
            goal_timeout_sec=max(self.timeout_sec, 30.0),
            result_timeout_sec=max(self.timeout_sec, 3600.0),
        )

    def get_benchmark_status(self, run_id: str) -> GatewayResponse:
        return self._call_service(
            GetBenchmarkStatus,
            "/benchmark/get_status",
            request_builder=lambda request: setattr(request, "run_id", run_id),
            response_builder=lambda response: GatewayResponse(
                True,
                "ok",
                {
                    "run_id": response.status.run_id,
                    "state": response.status.state,
                    "progress": float(response.status.progress),
                    "total_samples": int(response.status.total_samples),
                    "processed_samples": int(response.status.processed_samples),
                    "failed_samples": int(response.status.failed_samples),
                    "status_message": response.status.status_message,
                    "error_message": response.status.error_message,
                },
            ),
            unavailable_message="benchmark status service unavailable",
            no_response_message="No benchmark status response",
        )

    def get_runtime_status(self) -> GatewayResponse:
        return self._call_service(
            GetAsrStatus,
            "/asr/runtime/get_status",
            request_builder=lambda _request: None,
            response_builder=lambda response: GatewayResponse(
                True,
                "ok",
                {
                    "backend": response.backend,
                    "model": response.model,
                    "region": response.region,
                    "capabilities": list(response.capabilities),
                    "streaming_supported": bool(response.streaming_supported),
                    "streaming_mode": str(response.streaming_mode),
                    "cloud_credentials_available": bool(response.cloud_credentials_available),
                    "status_message": response.status_message,
                    "session_id": response.session_id,
                    "session_state": response.session_state,
                    "processing_mode": str(response.processing_mode),
                    "audio_source": response.audio_source,
                    "runtime_profile": response.runtime_profile,
                },
            ),
            unavailable_message="runtime status service unavailable",
            no_response_message="No runtime status response",
        )

    def list_backends(self) -> GatewayResponse:
        return self._call_service(
            ListBackends,
            "/asr/runtime/list_backends",
            request_builder=lambda _request: None,
            response_builder=lambda response: GatewayResponse(
                True,
                "ok",
                {"provider_ids": list(response.provider_ids)},
            ),
            unavailable_message="list backends service unavailable",
            no_response_message="No list backends response",
        )

    def register_dataset(
        self, manifest_path: str, dataset_id: str, dataset_profile: str
    ) -> GatewayResponse:
        def _build_request(request: Any) -> None:
            request.manifest_path = manifest_path
            request.dataset_id = dataset_id
            request.dataset_profile = dataset_profile

        return self._call_service(
            RegisterDataset,
            "/datasets/register",
            request_builder=_build_request,
            response_builder=lambda response: GatewayResponse(
                bool(response.success),
                response.message,
                {"dataset_id": response.dataset_id},
            ),
            unavailable_message="register dataset service unavailable",
            no_response_message="No register dataset response",
        )

    def import_dataset(
        self,
        *,
        source_path: str,
        dataset_id: str,
        dataset_profile: str,
    ) -> GatewayResponse:
        def _build_goal(goal: Any) -> None:
            goal.source_path = source_path
            goal.dataset_id = dataset_id
            goal.dataset_profile = dataset_profile

        return self._call_action(
            ImportDataset,
            "/datasets/import",
            goal_builder=_build_goal,
            result_builder=lambda result: GatewayResponse(
                bool(result.result.success),
                result.result.message,
                {
                    "dataset_id": result.result.dataset_id,
                    "manifest_ref": result.result.manifest_ref,
                    "success": bool(result.result.success),
                },
            ),
            unavailable_message="dataset import action server unavailable",
            goal_timeout_message="Timed out waiting for dataset import goal response",
            goal_rejected_message="Dataset import goal not accepted",
            result_timeout_message="Timed out waiting for dataset import result",
            no_result_message="No dataset import result",
        )

    def list_datasets(self) -> GatewayResponse:
        return self._call_service(
            ListDatasets,
            "/datasets/list",
            request_builder=lambda _request: None,
            response_builder=lambda response: GatewayResponse(
                True,
                "ok",
                {
                    "dataset_ids": list(response.dataset_ids),
                    "manifest_refs": list(response.dataset_manifest_refs),
                },
            ),
            unavailable_message="list datasets service unavailable",
            no_response_message="No list datasets response",
        )

    def validate_config(self, profile_type: str, profile_id: str) -> GatewayResponse:
        def _build_request(request: Any) -> None:
            request.profile_type = profile_type
            request.profile_id = profile_id
            request.config_path = ""

        return self._call_service(
            ValidateConfig,
            "/config/validate",
            request_builder=_build_request,
            response_builder=lambda response: GatewayResponse(
                bool(response.valid),
                response.message,
                {"resolved_config_ref": response.resolved_config_ref},
            ),
            unavailable_message="validate config service unavailable",
            no_response_message="No validate config response",
        )
