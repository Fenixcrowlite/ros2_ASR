from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "ros2_ws" / "src"

sys.path.insert(0, str(ROOT))
for package_root in SRC_ROOT.iterdir():
    if package_root.is_dir():
        sys.path.insert(0, str(package_root))


def _install_rclpy_stub() -> None:
    if "rclpy" in sys.modules:
        return

    rclpy = types.ModuleType("rclpy")
    rclpy.__asr_stub__ = True
    rclpy.init = lambda args=None: None
    rclpy.ok = lambda: True
    rclpy.shutdown = lambda: None
    rclpy.spin_until_future_complete = lambda node, future, timeout_sec=None: None

    action_mod = types.ModuleType("rclpy.action")
    executors_mod = types.ModuleType("rclpy.executors")
    node_mod = types.ModuleType("rclpy.node")
    qos_mod = types.ModuleType("rclpy.qos")

    class _Node:
        def __init__(self, name: str, **kwargs) -> None:
            del kwargs
            self.name = name
            self._parameters: dict[str, object] = {}

        def declare_parameter(self, name: str, value=None):
            self._parameters[name] = value
            return types.SimpleNamespace(name=name, value=value)

        def get_parameter(self, name: str):
            return types.SimpleNamespace(value=self._parameters.get(name), name=name)

        def create_client(self, *args, **kwargs):
            raise RuntimeError("rclpy client stub should not be used in non-ROS tests")

        def create_service(self, *args, **kwargs):
            del args, kwargs
            return None

        def create_publisher(self, *args, **kwargs):
            del args, kwargs
            return types.SimpleNamespace(publish=lambda message: message)

        def create_timer(self, *args, **kwargs):
            del args, kwargs
            return None

        def create_subscription(self, *args, **kwargs):
            return None

        def destroy_node(self) -> None:
            return None

    class _ActionClient:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def wait_for_server(self, timeout_sec=None) -> bool:
            return False

    class _ActionServer:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            return None

    class _SingleThreadedExecutor:
        def add_node(self, node) -> None:
            del node
            return None

        def spin_once(self, timeout_sec=None) -> None:
            del timeout_sec
            return None

        def spin(self) -> None:
            return None

        def shutdown(self, timeout_sec=None) -> None:
            del timeout_sec
            return None

    class _MultiThreadedExecutor(_SingleThreadedExecutor):
        pass

    class _ExternalShutdownException(Exception):
        pass

    class _ReliabilityPolicy:
        RELIABLE = "reliable"

    class _DurabilityPolicy:
        VOLATILE = "volatile"
        TRANSIENT_LOCAL = "transient_local"

    class _QoSProfile:
        def __init__(self, depth: int = 10, reliability=None, durability=None) -> None:
            self.depth = depth
            self.reliability = reliability
            self.durability = durability

    node_mod.Node = _Node
    action_mod.ActionClient = _ActionClient
    action_mod.ActionServer = _ActionServer
    executors_mod.SingleThreadedExecutor = _SingleThreadedExecutor
    executors_mod.MultiThreadedExecutor = _MultiThreadedExecutor
    executors_mod.ExternalShutdownException = _ExternalShutdownException
    qos_mod.ReliabilityPolicy = _ReliabilityPolicy
    qos_mod.DurabilityPolicy = _DurabilityPolicy
    qos_mod.QoSProfile = _QoSProfile
    rclpy.create_node = lambda name, **kwargs: _Node(name, **kwargs)
    rclpy.node = node_mod
    rclpy.action = action_mod
    rclpy.executors = executors_mod
    rclpy.qos = qos_mod

    sys.modules["rclpy"] = rclpy
    sys.modules["rclpy.node"] = node_mod
    sys.modules["rclpy.action"] = action_mod
    sys.modules["rclpy.executors"] = executors_mod
    sys.modules["rclpy.qos"] = qos_mod


def _install_asr_interfaces_stub() -> None:
    if "asr_interfaces" in sys.modules:
        return

    root_mod = types.ModuleType("asr_interfaces")
    action_mod = types.ModuleType("asr_interfaces.action")
    msg_mod = types.ModuleType("asr_interfaces.msg")
    srv_mod = types.ModuleType("asr_interfaces.srv")

    class _Header:
        def __init__(self) -> None:
            self.stamp = None

    class _Dummy:
        def __init__(self) -> None:
            self.header = _Header()
            self.data = []

        class Goal:
            pass

        class Request:
            pass

        class Response:
            pass

        class Feedback:
            pass

        class Result:
            pass

    for name in ("ImportDataset", "RunBenchmarkExperiment", "Transcribe"):
        setattr(action_mod, name, _Dummy)
    for name in (
        "AsrMetrics",
        "AsrResult",
        "AsrResultPartial",
        "AudioChunk",
        "AudioSegment",
        "BenchmarkJobStatus",
        "DatasetStatus",
        "ExperimentSummary",
        "NodeStatus",
        "SessionStatus",
        "SpeechActivity",
        "WordTimestamp",
    ):
        setattr(msg_mod, name, _Dummy)
    for name in (
        "GetAsrStatus",
        "GetBenchmarkStatus",
        "ListBackends",
        "ListDatasets",
        "ListProfiles",
        "RecognizeOnce",
        "RegisterDataset",
        "ReconfigureRuntime",
        "SetAsrBackend",
        "StartRuntimeSession",
        "StopRuntimeSession",
        "ValidateConfig",
    ):
        setattr(srv_mod, name, _Dummy)

    root_mod.action = action_mod
    root_mod.msg = msg_mod
    root_mod.srv = srv_mod
    sys.modules["asr_interfaces"] = root_mod
    sys.modules["asr_interfaces.action"] = action_mod
    sys.modules["asr_interfaces.msg"] = msg_mod
    sys.modules["asr_interfaces.srv"] = srv_mod


def _install_rcl_interfaces_stub() -> None:
    if "rcl_interfaces.msg" in sys.modules:
        return

    root_mod = types.ModuleType("rcl_interfaces")
    msg_mod = types.ModuleType("rcl_interfaces.msg")

    class _ParameterDescriptor:
        def __init__(self, **kwargs) -> None:
            del kwargs

    msg_mod.ParameterDescriptor = _ParameterDescriptor
    root_mod.msg = msg_mod
    sys.modules["rcl_interfaces"] = root_mod
    sys.modules["rcl_interfaces.msg"] = msg_mod


def _install_std_msgs_stub() -> None:
    if "std_msgs.msg" in sys.modules:
        return

    root_mod = types.ModuleType("std_msgs")
    msg_mod = types.ModuleType("std_msgs.msg")

    class _UInt8MultiArray:
        def __init__(self) -> None:
            self.data = []

    msg_mod.UInt8MultiArray = _UInt8MultiArray
    root_mod.msg = msg_mod
    sys.modules["std_msgs"] = root_mod
    sys.modules["std_msgs.msg"] = msg_mod


def _install_builtin_interfaces_stub() -> None:
    if "builtin_interfaces.msg" in sys.modules:
        return

    root_mod = types.ModuleType("builtin_interfaces")
    msg_mod = types.ModuleType("builtin_interfaces.msg")

    class _Time:
        def __init__(self) -> None:
            self.sec = 0
            self.nanosec = 0

    msg_mod.Time = _Time
    root_mod.msg = msg_mod
    sys.modules["builtin_interfaces"] = root_mod
    sys.modules["builtin_interfaces.msg"] = msg_mod


try:
    import rclpy  # type: ignore[import-not-found]  # noqa: F401
except ModuleNotFoundError:
    _install_rclpy_stub()

try:
    import asr_interfaces.action  # type: ignore[import-not-found]  # noqa: F401
    import asr_interfaces.msg  # type: ignore[import-not-found]  # noqa: F401
    import asr_interfaces.srv  # type: ignore[import-not-found]  # noqa: F401
except ModuleNotFoundError:
    _install_asr_interfaces_stub()

try:
    import builtin_interfaces.msg  # type: ignore[import-not-found]  # noqa: F401
except ModuleNotFoundError:
    _install_builtin_interfaces_stub()

try:
    import rcl_interfaces.msg  # type: ignore[import-not-found]  # noqa: F401
except ModuleNotFoundError:
    _install_rcl_interfaces_stub()

try:
    import std_msgs.msg  # type: ignore[import-not-found]  # noqa: F401
except ModuleNotFoundError:
    _install_std_msgs_stub()


@pytest.fixture(scope="session")
def sample_wav() -> str:
    return str(ROOT / "data" / "sample" / "vosk_test.wav")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture()
def isolated_ros_domain(monkeypatch: pytest.MonkeyPatch) -> str:
    domain_id = str(200 + (os.getpid() % 20))
    monkeypatch.setenv("ROS_DOMAIN_ID", domain_id)
    return domain_id


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    path_markers = {
        "tests/unit/": pytest.mark.unit,
        "tests/component/": pytest.mark.component,
        "tests/contract/": pytest.mark.contract,
        "tests/api/": pytest.mark.api,
        "tests/gui/": pytest.mark.gui,
        "tests/e2e/": pytest.mark.e2e,
        "tests/integration/": pytest.mark.integration,
        "tests/regression/": pytest.mark.regression,
        "tests/ros2/": pytest.mark.ros,
    }

    for item in items:
        path = str(item.fspath)
        for marker_path, marker in path_markers.items():
            if marker_path in path:
                item.add_marker(marker)
