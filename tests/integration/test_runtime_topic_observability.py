from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.ros


def test_runtime_final_results_are_retained_for_late_subscribers(
    monkeypatch,
    isolated_ros_domain: str,
) -> None:
    del isolated_ros_domain
    import rclpy
    if getattr(rclpy, "__asr_stub__", False):
        pytest.skip("ROS integration test requires sourced ROS Jazzy workspace")
    import asr_runtime_nodes.asr_orchestrator_node as orchestrator_module
    from asr_interfaces.msg import AsrResult
    from asr_runtime_nodes.asr_orchestrator_node import AsrOrchestratorNode
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

    from tests.utils.fakes import build_stub_provider_manager, make_normalized_result

    monkeypatch.setattr(
        orchestrator_module,
        "ProviderManager",
        build_stub_provider_manager(str(Path("configs"))),
    )

    rclpy.init()
    server = AsrOrchestratorNode()
    executor = MultiThreadedExecutor()
    executor.add_node(server)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    client_node = None
    try:
        published = make_normalized_result(
            provider_id="whisper",
            session_id=server.session_id,
            request_id="req_retained_final",
            text="retained transcript",
        )
        server._publish_result(published)
        time.sleep(0.3)

        client_node = rclpy.create_node("late_result_observer")
        received: list[AsrResult] = []
        client_node.create_subscription(
            AsrResult,
            "/asr/runtime/results/final",
            lambda msg: received.append(msg),
            QoSProfile(
                depth=10,
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
            ),
        )

        timeout_at = time.time() + 5.0
        while time.time() < timeout_at and not received:
            rclpy.spin_once(client_node, timeout_sec=0.2)

        assert received
        assert received[0].request_id == published.request_id
        assert received[0].text == published.text
    finally:
        executor.shutdown()
        server.destroy_node()
        if client_node is not None:
            client_node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
