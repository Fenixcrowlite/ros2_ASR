from __future__ import annotations

import threading
from types import SimpleNamespace

import asr_gateway.ros_client as ros_client_module
from asr_gateway.ros_client import GatewayResponse, GatewayRosClient, RuntimeObserver


class _DoneFuture:
    def __init__(self, result):
        self._result = result

    def done(self) -> bool:
        return True

    def result(self):
        return self._result


class _FakeServiceClient:
    def __init__(self, *, result, available: bool = True) -> None:
        self._result = result
        self._available = available
        self.requests = []

    def wait_for_service(self, timeout_sec=None) -> bool:
        del timeout_sec
        return self._available

    def call_async(self, request):
        self.requests.append(request)
        return _DoneFuture(self._result)


class _FakeNode:
    def __init__(self, service_client: _FakeServiceClient) -> None:
        self.service_client = service_client
        self.destroyed = False
        self.last_service = ("", "")
        self.create_client_calls = 0

    def create_client(self, service_type, service_name):
        self.last_service = (service_type, service_name)
        self.create_client_calls += 1
        return self.service_client

    def destroy_node(self) -> None:
        self.destroyed = True


class _FakeGoalHandle:
    def __init__(self, *, accepted: bool, result) -> None:
        self.accepted = accepted
        self._result = result

    def get_result_async(self):
        return _DoneFuture(self._result)


class _FakeActionClient:
    def __init__(self, node, action_type, action_name) -> None:
        del action_type
        self.node = node
        self.action_name = action_name
        self.available = True
        self.goal = None
        self.goal_handle = _FakeGoalHandle(accepted=True, result=None)

    def wait_for_server(self, timeout_sec=None) -> bool:
        del timeout_sec
        return self.available

    def send_goal_async(self, goal):
        self.goal = goal
        return _DoneFuture(self.goal_handle)


class _RaisingExecutor:
    def shutdown(self, timeout_sec=None) -> None:
        del timeout_sec
        raise RuntimeError("executor shutdown boom")


class _RaisingNodeForStop:
    def destroy_node(self) -> None:
        raise RuntimeError("destroy boom")


class _FakeThread:
    def __init__(self, *, alive: bool = False) -> None:
        self.alive = alive
        self.join_calls = []

    def join(self, timeout=None) -> None:
        self.join_calls.append(timeout)

    def is_alive(self) -> bool:
        return self.alive


def _make_client_with_node(node: _FakeNode) -> GatewayRosClient:
    client = object.__new__(GatewayRosClient)
    client.timeout_sec = 5.0
    client._bridge_lock = threading.Lock()
    client._service_clients = {}
    client._action_clients = {}
    client._client_node = node
    client._executor = None
    client._executor_thread = None
    client._observer = SimpleNamespace(
        snapshot=lambda: {},
        record_result=lambda payload: payload,
        stop=lambda: None,
    )
    client._node = lambda: node
    client._await_future = lambda _node, _future, timeout_sec: bool(timeout_sec)
    return client


def test_start_runtime_populates_request_and_maps_response() -> None:
    service_response = SimpleNamespace(
        accepted=True,
        message="started",
        session_id="session_demo",
        resolved_config_ref="configs/resolved/runtime__demo.json",
    )
    service_client = _FakeServiceClient(result=service_response)
    node = _FakeNode(service_client)
    client = _make_client_with_node(node)

    response = client.start_runtime(
        "default_runtime",
        "providers/whisper_local",
        "session_demo",
        processing_mode="provider_stream",
        provider_preset="accurate",
        provider_settings={"beam_size": 5},
        audio_source="file",
        audio_file_path="data/sample/vosk_test.wav",
        language="en-US",
        mic_capture_sec=4.0,
    )

    request = service_client.requests[0]
    assert node.last_service[1] == "/asr/runtime/start_session"
    assert request.runtime_profile == "default_runtime"
    assert request.provider_profile == "providers/whisper_local"
    assert request.provider_preset == "accurate"
    assert request.provider_settings_json == '{"beam_size": 5}'
    assert request.runtime_namespace == "/asr/runtime"
    assert request.auto_start_audio is True
    assert response.success is True
    assert response.payload["session_id"] == "session_demo"


def test_list_backends_returns_service_unavailable_without_calling_async() -> None:
    service_client = _FakeServiceClient(result=None, available=False)
    node = _FakeNode(service_client)
    client = _make_client_with_node(node)

    response = client.list_backends()

    assert response.success is False
    assert response.message == "list backends service unavailable"
    assert service_client.requests == []
    assert node.create_client_calls == 1


def test_run_benchmark_uses_action_helper_and_maps_summary(monkeypatch) -> None:
    fake_action = _FakeActionClient(None, None, "/benchmark/run_experiment")
    benchmark_result = SimpleNamespace(
        result=SimpleNamespace(
            run_id="bench_demo",
            success=True,
            message="completed",
            summary=SimpleNamespace(
                total_samples=10,
                successful_samples=9,
                failed_samples=1,
                mean_wer=0.12,
                mean_cer=0.04,
                mean_latency_ms=321.0,
                summary_artifact_ref="artifacts/benchmark_runs/bench_demo/summary.json",
            ),
        )
    )
    fake_action.goal_handle = _FakeGoalHandle(accepted=True, result=benchmark_result)
    monkeypatch.setattr(
        ros_client_module,
        "ActionClient",
        lambda node, action_type, action_name: fake_action,
    )

    node = _FakeNode(_FakeServiceClient(result=None))
    client = _make_client_with_node(node)

    response = client.run_benchmark(
        "default_benchmark",
        "sample_dataset",
        ["providers/whisper_local"],
        scenario="noise_robustness",
        provider_overrides={"providers/whisper_local": {"provider_preset": "accurate"}},
        benchmark_settings={"execution_mode": "streaming"},
        run_id="bench_demo",
    )

    assert fake_action.action_name == "/benchmark/run_experiment"
    assert fake_action.goal.benchmark_profile == "default_benchmark"
    assert fake_action.goal.provider_overrides_json == (
        '{"providers/whisper_local": {"provider_preset": "accurate"}}'
    )
    assert fake_action.goal.benchmark_settings_json == '{"execution_mode": "streaming"}'
    assert response.success is True
    assert response.payload["summary"]["total_samples"] == 10
    assert response.payload["action_latency_ms"] >= 0.0
    assert response.payload["ros_action_latency_ms"] >= 0.0
    assert response.payload["action_goal_wait_ms"] >= 0.0
    assert response.payload["action_result_wait_ms"] >= 0.0


def test_run_benchmark_uses_extended_goal_and_result_timeouts() -> None:
    node = _FakeNode(_FakeServiceClient(result=None))
    client = _make_client_with_node(node)
    captured: dict[str, object] = {}

    def fake_call_action(*args, **kwargs):
        del args
        captured.update(kwargs)
        return GatewayResponse(True, "queued", {})

    client._call_action = fake_call_action

    response = client.run_benchmark(
        "default_benchmark",
        "sample_dataset",
        ["providers/whisper_local"],
        run_id="bench_timeout_contract",
    )

    assert response.success is True
    assert captured["goal_timeout_sec"] == 30.0
    assert captured["result_timeout_sec"] == 3600.0


def test_service_clients_are_reused_across_calls() -> None:
    service_client = _FakeServiceClient(
        result=SimpleNamespace(provider_ids=["whisper", "azure"]),
    )
    node = _FakeNode(service_client)
    client = _make_client_with_node(node)

    first = client.list_backends()
    second = client.list_backends()

    assert first.success is True
    assert second.success is True
    assert node.create_client_calls == 1


def test_close_shuts_down_persistent_bridge() -> None:
    stop_calls: list[str] = []
    executor = SimpleNamespace(shutdown=lambda timeout_sec=None: stop_calls.append(f"executor:{timeout_sec}"))
    node = _FakeNode(_FakeServiceClient(result=None))
    thread = _FakeThread(alive=False)
    client = object.__new__(GatewayRosClient)
    client._observer = SimpleNamespace(stop=lambda: stop_calls.append("observer"))
    client._executor = executor
    client._client_node = node
    client._executor_thread = thread
    client._service_clients = {"svc": object()}
    client._action_clients = {"act": object()}

    GatewayRosClient.close(client)

    assert stop_calls[0] == "observer"
    assert stop_calls[1] == "executor:0.5"
    assert node.destroyed is True
    assert thread.join_calls == [0.5]
    assert client._executor is None
    assert client._client_node is None
    assert client._executor_thread is None
    assert client._service_clients == {}
    assert client._action_clients == {}


def test_runtime_observer_stop_records_cleanup_failures() -> None:
    observer = RuntimeObserver()
    observer._executor = _RaisingExecutor()
    observer._node = _RaisingNodeForStop()
    observer._thread = _FakeThread(alive=True)
    observer._started = True

    observer.stop()

    assert "observer_shutdown_failed: executor shutdown boom" in observer._error
    assert "observer_destroy_node_failed: destroy boom" in observer._error
    assert "observer_join_failed: observer thread did not stop" in observer._error
    assert observer._started is False
    assert observer._executor is None
    assert observer._node is None
    assert observer._thread is None


def test_runtime_observer_start_failure_resets_partial_state(monkeypatch) -> None:
    class _BrokenNode:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            raise RuntimeError("node create failed")

    monkeypatch.setattr(ros_client_module, "Node", _BrokenNode)
    observer = RuntimeObserver()

    observer.start()

    assert "observer_start_failed: node create failed" in observer._error
    assert observer._started is False
    assert observer._executor is None
    assert observer._node is None
    assert observer._thread is None
