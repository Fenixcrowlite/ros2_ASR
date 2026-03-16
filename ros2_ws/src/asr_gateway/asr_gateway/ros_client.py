"""ROS2 client facade for gateway operations."""

from __future__ import annotations

import json
import threading
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
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
    RegisterDataset,
    ReconfigureRuntime,
    StartRuntimeSession,
    StopRuntimeSession,
    ValidateConfig,
)
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


@dataclass(slots=True)
class GatewayResponse:
    success: bool
    message: str
    payload: dict


def _stamp_to_iso(stamp: Any) -> str:
    sec = int(getattr(stamp, "sec", 0) or 0)
    nanosec = int(getattr(stamp, "nanosec", 0) or 0)
    if sec <= 0 and nanosec <= 0:
        return ""
    return datetime.fromtimestamp(sec + (nanosec / 1_000_000_000.0), tz=timezone.utc).isoformat()


class RuntimeObserver:
    """Background ROS subscriber collecting live runtime signals for the gateway."""

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

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        try:
            self._node = Node("asr_gateway_runtime_observer", use_global_arguments=False)
            self._node.create_subscription(AsrResult, TOPICS["final_results"], self._on_final_result, 10)
            self._node.create_subscription(AsrResultPartial, TOPICS["partial_results"], self._on_partial_result, 10)
            self._node.create_subscription(NodeStatus, TOPICS["node_status"], self._on_node_status, 10)
            self._node.create_subscription(SessionStatus, TOPICS["session_status"], self._on_session_status, 10)
            self._executor = SingleThreadedExecutor()
            self._executor.add_node(self._node)
            self._thread = threading.Thread(target=self._spin, name="asr-gateway-runtime-observer", daemon=True)
            self._thread.start()
        except Exception as exc:
            self._error = str(exc)

    def _spin(self) -> None:
        if self._executor is None:
            return
        try:
            self._executor.spin()
        except Exception as exc:
            self._error = str(exc)

    def stop(self) -> None:
        try:
            if self._executor is not None:
                self._executor.shutdown(timeout_sec=0.5)
        except Exception:
            pass
        try:
            if self._node is not None:
                self._node.destroy_node()
        except Exception:
            pass
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
        unique_value = str(item.get(unique_key, "") or "").strip()
        if unique_value:
            deduped = [row for row in queue_ref if str(row.get(unique_key, "") or "").strip() != unique_value]
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
            "time": datetime.now(timezone.utc).isoformat(),
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
                "node_statuses": sorted(self._node_statuses.values(), key=lambda item: item["node_name"]),
                "session_statuses": sessions,
                "active_session": sessions[0] if sessions else {},
            }


class GatewayRosClient:
    """Synchronous helper around ROS services/actions for gateway endpoints."""

    def __init__(self, timeout_sec: float = 5.0) -> None:
        self.timeout_sec = timeout_sec
        if not rclpy.ok():
            rclpy.init(args=None)
        self._observer = RuntimeObserver()
        self._observer.start()

    def close(self) -> None:
        self._observer.stop()

    def _node(self) -> Node:
        return Node(f"asr_gateway_client_{uuid.uuid4().hex[:8]}", use_global_arguments=False)

    def _await_future(self, node: Node, future: Any, *, timeout_sec: float) -> bool:
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        try:
            deadline = datetime.now(timezone.utc).timestamp() + timeout_sec
            while not future.done():
                remaining = deadline - datetime.now(timezone.utc).timestamp()
                if remaining <= 0:
                    return False
                executor.spin_once(timeout_sec=min(0.2, remaining))
            return True
        finally:
            try:
                executor.shutdown(timeout_sec=0.1)
            except Exception:
                pass

    def runtime_snapshot(self) -> dict[str, Any]:
        return self._observer.snapshot()

    def record_runtime_result(self, payload: dict[str, Any]) -> None:
        self._observer.record_result(payload)

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
        node = self._node()
        try:
            client = node.create_client(StartRuntimeSession, "/asr/runtime/start_session")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "start_session service unavailable", {})
            req = StartRuntimeSession.Request()
            req.runtime_profile = runtime_profile
            req.provider_profile = provider_profile
            req.provider_preset = provider_preset
            req.provider_settings_json = json.dumps(provider_settings or {}, ensure_ascii=True)
            req.session_id = session_id
            req.runtime_namespace = "/asr/runtime"
            req.auto_start_audio = True
            req.processing_mode = processing_mode
            req.audio_source = audio_source
            req.audio_file_path = audio_file_path
            req.language = language
            req.mic_capture_sec = float(mic_capture_sec)
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No response from start_session", {})
            res = fut.result()
            return GatewayResponse(
                bool(res.accepted),
                res.message,
                {
                    "session_id": res.session_id,
                    "resolved": res.resolved_config_ref,
                },
            )
        finally:
            node.destroy_node()

    def stop_runtime(self, session_id: str) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(StopRuntimeSession, "/asr/runtime/stop_session")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "stop_session service unavailable", {})
            req = StopRuntimeSession.Request()
            req.session_id = session_id
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No response from stop_session", {})
            res = fut.result()
            return GatewayResponse(bool(res.success), res.message, {})
        finally:
            node.destroy_node()

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
        node = self._node()
        try:
            client = node.create_client(ReconfigureRuntime, "/asr/runtime/reconfigure")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "reconfigure service unavailable", {})
            req = ReconfigureRuntime.Request()
            req.session_id = session_id
            req.runtime_profile = runtime_profile
            req.provider_profile = provider_profile
            req.provider_preset = provider_preset
            req.provider_settings_json = json.dumps(provider_settings or {}, ensure_ascii=True)
            req.processing_mode = processing_mode
            req.audio_source = audio_source
            req.audio_file_path = audio_file_path
            req.language = language
            req.mic_capture_sec = float(mic_capture_sec)
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No response from reconfigure", {})
            res = fut.result()
            return GatewayResponse(bool(res.success), res.message, {"resolved": res.resolved_config_ref})
        finally:
            node.destroy_node()

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
        node = self._node()
        try:
            client = node.create_client(RecognizeOnce, "/asr/runtime/recognize_once")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "recognize_once service unavailable", {})
            req = RecognizeOnce.Request()
            req.wav_path = wav_path
            req.language = language
            req.enable_word_timestamps = True
            req.session_id = session_id
            req.provider_profile = provider_profile
            req.provider_preset = provider_preset
            req.provider_settings_json = json.dumps(provider_settings or {}, ensure_ascii=True)
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=max(self.timeout_sec, 20.0)) or fut.result() is None:
                return GatewayResponse(False, "No response from recognize_once", {})
            res = fut.result()
            payload = {
                "request_id": res.result.request_id,
                "session_id": res.result.session_id,
                "text": res.result.text,
                "provider_id": res.result.provider_id,
                "success": bool(res.result.success),
                "error_code": res.result.error_code,
                "error_message": res.result.error_message,
                "language": res.result.language,
                "latency_ms": float(res.result.total_ms),
                "degraded": bool(res.result.degraded),
                "raw_metadata_ref": res.result.raw_metadata_ref,
                "resolved_profile": res.resolved_profile,
            }
            return GatewayResponse(bool(res.result.success), "ok", payload)
        finally:
            node.destroy_node()

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
        node = self._node()
        try:
            action = ActionClient(node, RunBenchmarkExperiment, "/benchmark/run_experiment")
            if not action.wait_for_server(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "benchmark action server unavailable", {})

            goal = RunBenchmarkExperiment.Goal()
            goal.benchmark_profile = benchmark_profile
            goal.dataset_profile = dataset_profile
            goal.run_id = run_id
            goal.providers = providers
            goal.scenario = scenario
            goal.provider_overrides_json = json.dumps(provider_overrides or {}, ensure_ascii=True)
            goal.benchmark_settings_json = json.dumps(benchmark_settings or {}, ensure_ascii=True)

            send_future = action.send_goal_async(goal)
            if not self._await_future(node, send_future, timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "Timed out waiting for benchmark goal response", {})
            goal_handle = send_future.result()
            if goal_handle is None or not goal_handle.accepted:
                return GatewayResponse(False, "Benchmark goal not accepted", {})

            result_future = goal_handle.get_result_async()
            if not self._await_future(node, result_future, timeout_sec=180.0):
                return GatewayResponse(False, "Timed out waiting for benchmark result", {})
            result = result_future.result()
            if result is None:
                return GatewayResponse(False, "No benchmark result", {})
            payload = {
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
            }
            return GatewayResponse(bool(result.result.success), result.result.message, payload)
        finally:
            node.destroy_node()

    def get_benchmark_status(self, run_id: str) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(GetBenchmarkStatus, "/benchmark/get_status")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "benchmark status service unavailable", {})
            req = GetBenchmarkStatus.Request()
            req.run_id = run_id
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No benchmark status response", {})
            status = fut.result().status
            payload = {
                "run_id": status.run_id,
                "state": status.state,
                "progress": float(status.progress),
                "total_samples": int(status.total_samples),
                "processed_samples": int(status.processed_samples),
                "failed_samples": int(status.failed_samples),
                "status_message": status.status_message,
                "error_message": status.error_message,
            }
            return GatewayResponse(True, "ok", payload)
        finally:
            node.destroy_node()

    def get_runtime_status(self) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(GetAsrStatus, "/asr/runtime/get_status")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "runtime status service unavailable", {})
            req = GetAsrStatus.Request()
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No runtime status response", {})
            res = fut.result()
            payload = {
                "backend": res.backend,
                "model": res.model,
                "region": res.region,
                "capabilities": list(res.capabilities),
                "streaming_supported": bool(res.streaming_supported),
                "streaming_mode": str(res.streaming_mode),
                "cloud_credentials_available": bool(res.cloud_credentials_available),
                "status_message": res.status_message,
                "session_id": res.session_id,
                "session_state": res.session_state,
                "processing_mode": str(res.processing_mode),
                "audio_source": res.audio_source,
                "runtime_profile": res.runtime_profile,
            }
            return GatewayResponse(True, "ok", payload)
        finally:
            node.destroy_node()

    def list_backends(self) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(ListBackends, "/asr/runtime/list_backends")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "list backends service unavailable", {})
            req = ListBackends.Request()
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No list backends response", {})
            res = fut.result()
            return GatewayResponse(True, "ok", {"provider_ids": list(res.provider_ids)})
        finally:
            node.destroy_node()

    def register_dataset(self, manifest_path: str, dataset_id: str, dataset_profile: str) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(RegisterDataset, "/datasets/register")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "register dataset service unavailable", {})
            req = RegisterDataset.Request()
            req.manifest_path = manifest_path
            req.dataset_id = dataset_id
            req.dataset_profile = dataset_profile
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No register dataset response", {})
            res = fut.result()
            return GatewayResponse(bool(res.success), res.message, {"dataset_id": res.dataset_id})
        finally:
            node.destroy_node()

    def import_dataset(
        self,
        *,
        source_path: str,
        dataset_id: str,
        dataset_profile: str,
    ) -> GatewayResponse:
        node = self._node()
        try:
            action = ActionClient(node, ImportDataset, "/datasets/import")
            if not action.wait_for_server(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "dataset import action server unavailable", {})

            goal = ImportDataset.Goal()
            goal.source_path = source_path
            goal.dataset_id = dataset_id
            goal.dataset_profile = dataset_profile

            send_future = action.send_goal_async(goal)
            if not self._await_future(node, send_future, timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "Timed out waiting for dataset import goal response", {})
            goal_handle = send_future.result()
            if goal_handle is None or not goal_handle.accepted:
                return GatewayResponse(False, "Dataset import goal not accepted", {})

            result_future = goal_handle.get_result_async()
            if not self._await_future(node, result_future, timeout_sec=180.0):
                return GatewayResponse(False, "Timed out waiting for dataset import result", {})
            result = result_future.result()
            if result is None:
                return GatewayResponse(False, "No dataset import result", {})
            payload = {
                "dataset_id": result.result.dataset_id,
                "manifest_ref": result.result.manifest_ref,
                "success": bool(result.result.success),
            }
            return GatewayResponse(bool(result.result.success), result.result.message, payload)
        finally:
            node.destroy_node()

    def list_datasets(self) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(ListDatasets, "/datasets/list")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "list datasets service unavailable", {})
            req = ListDatasets.Request()
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No list datasets response", {})
            res = fut.result()
            return GatewayResponse(
                True,
                "ok",
                {
                    "dataset_ids": list(res.dataset_ids),
                    "manifest_refs": list(res.dataset_manifest_refs),
                },
            )
        finally:
            node.destroy_node()

    def validate_config(self, profile_type: str, profile_id: str) -> GatewayResponse:
        node = self._node()
        try:
            client = node.create_client(ValidateConfig, "/config/validate")
            if not client.wait_for_service(timeout_sec=self.timeout_sec):
                return GatewayResponse(False, "validate config service unavailable", {})
            req = ValidateConfig.Request()
            req.profile_type = profile_type
            req.profile_id = profile_id
            req.config_path = ""
            fut = client.call_async(req)
            if not self._await_future(node, fut, timeout_sec=self.timeout_sec) or fut.result() is None:
                return GatewayResponse(False, "No validate config response", {})
            res = fut.result()
            return GatewayResponse(
                bool(res.valid),
                res.message,
                {"resolved_config_ref": res.resolved_config_ref},
            )
        finally:
            node.destroy_node()
