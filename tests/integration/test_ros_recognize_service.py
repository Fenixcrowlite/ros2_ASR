from __future__ import annotations

import threading
import time

import pytest

pytestmark = pytest.mark.ros


def test_ros_recognize_once_service() -> None:
    rclpy = pytest.importorskip("rclpy")
    try:
        from asr_interfaces.srv import RecognizeOnce
    except Exception:
        pytest.skip("ROS interfaces are not built in current environment")

    from asr_ros.asr_server_node import AsrServerNode
    from rclpy.executors import MultiThreadedExecutor

    rclpy.init()
    server = AsrServerNode()
    client_node = rclpy.create_node("asr_test_client")
    client = client_node.create_client(RecognizeOnce, "/asr/recognize_once")

    executor = MultiThreadedExecutor()
    executor.add_node(server)
    executor.add_node(client_node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        assert client.wait_for_service(timeout_sec=5.0)
        req = RecognizeOnce.Request()
        req.wav_path = "data/sample/en_hello.wav"
        req.language = "sk"
        req.enable_word_timestamps = True

        future = client.call_async(req)
        timeout_at = time.time() + 10.0
        while time.time() < timeout_at and not future.done():
            time.sleep(0.1)
        assert future.done()

        result = future.result()
        assert result is not None
        assert result.result.success
        assert result.result.text != ""
    finally:
        executor.shutdown()
        server.destroy_node()
        client_node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
