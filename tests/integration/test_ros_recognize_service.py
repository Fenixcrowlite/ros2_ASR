from __future__ import annotations

import threading
import time

import pytest

pytestmark = pytest.mark.ros


def test_ros_recognize_once_service() -> None:
    import rclpy
    from asr_interfaces.srv import GetAsrStatus, RecognizeOnce, SetAsrBackend
    from asr_ros.asr_server_node import AsrServerNode
    from rclpy.executors import MultiThreadedExecutor

    rclpy.init()
    server = AsrServerNode()
    client_node = rclpy.create_node("asr_test_client")
    client = client_node.create_client(RecognizeOnce, "/asr/recognize_once")
    set_backend_client = client_node.create_client(SetAsrBackend, "/asr/set_backend")
    status_client = client_node.create_client(GetAsrStatus, "/asr/get_status")

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

        assert set_backend_client.wait_for_service(timeout_sec=5.0)
        set_req = SetAsrBackend.Request()
        set_req.backend = ""
        set_req.model = ""
        set_req.region = ""
        set_future = set_backend_client.call_async(set_req)
        timeout_at = time.time() + 10.0
        while time.time() < timeout_at and not set_future.done():
            time.sleep(0.1)
        assert set_future.done()
        set_result = set_future.result()
        assert set_result is not None
        assert not set_result.success

        assert status_client.wait_for_service(timeout_sec=5.0)
        status_future = status_client.call_async(GetAsrStatus.Request())
        timeout_at = time.time() + 10.0
        while time.time() < timeout_at and not status_future.done():
            time.sleep(0.1)
        assert status_future.done()
        status_result = status_future.result()
        assert status_result is not None
        assert status_result.backend == "mock"
    finally:
        executor.shutdown()
        server.destroy_node()
        client_node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
