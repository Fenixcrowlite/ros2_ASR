from __future__ import annotations

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
    rclpy.init = lambda args=None: None
    rclpy.ok = lambda: True
    rclpy.shutdown = lambda: None
    rclpy.spin_until_future_complete = lambda node, future, timeout_sec=None: None

    action_mod = types.ModuleType("rclpy.action")
    executors_mod = types.ModuleType("rclpy.executors")
    node_mod = types.ModuleType("rclpy.node")

    class _Node:
        def __init__(self, name: str, **kwargs) -> None:
            del kwargs
            self.name = name

        def create_client(self, *args, **kwargs):
            raise RuntimeError("rclpy client stub should not be used in non-ROS tests")

        def create_subscription(self, *args, **kwargs):
            return None

        def destroy_node(self) -> None:
            return None

    class _ActionClient:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def wait_for_server(self, timeout_sec=None) -> bool:
            return False

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

    node_mod.Node = _Node
    action_mod.ActionClient = _ActionClient
    executors_mod.SingleThreadedExecutor = _SingleThreadedExecutor
    rclpy.node = node_mod
    rclpy.action = action_mod
    rclpy.executors = executors_mod

    sys.modules["rclpy"] = rclpy
    sys.modules["rclpy.node"] = node_mod
    sys.modules["rclpy.action"] = action_mod
    sys.modules["rclpy.executors"] = executors_mod


def _install_asr_interfaces_stub() -> None:
    if "asr_interfaces" in sys.modules:
        return

    root_mod = types.ModuleType("asr_interfaces")
    action_mod = types.ModuleType("asr_interfaces.action")
    msg_mod = types.ModuleType("asr_interfaces.msg")
    srv_mod = types.ModuleType("asr_interfaces.srv")

    class _Dummy:
        class Goal:
            pass

        class Request:
            pass

    for name in ("ImportDataset", "RunBenchmarkExperiment"):
        setattr(action_mod, name, _Dummy)
    for name in ("AsrResult", "AsrResultPartial", "NodeStatus", "SessionStatus"):
        setattr(msg_mod, name, _Dummy)
    for name in (
        "GetAsrStatus",
        "GetBenchmarkStatus",
        "ListBackends",
        "ListDatasets",
        "RecognizeOnce",
        "RegisterDataset",
        "ReconfigureRuntime",
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


@pytest.fixture(scope="session")
def sample_wav() -> str:
    return str(ROOT / "data" / "sample" / "en_hello.wav")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


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
        "tests/unit/web_gui/": pytest.mark.legacy,
    }

    for item in items:
        path = str(item.fspath)
        for marker_path, marker in path_markers.items():
            if marker_path in path:
                item.add_marker(marker)
