"""Dedicated text output node.

Subscribes to structured ASR results and republishes plain text into a separate topic.
"""

from __future__ import annotations

import rclpy
from asr_interfaces.msg import AsrResult
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String


def _as_bool(value: object) -> bool:
    """Parse ROS parameter value that can be bool/string."""
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class AsrTextOutputNode(Node):
    """Relay `/asr/text` messages into plain-string topic `/asr/text/plain`."""

    def __init__(self) -> None:
        super().__init__("asr_text_output_node")
        self.declare_parameter("input_topic", "/asr/text")
        self.declare_parameter("output_topic", "/asr/text/plain")
        self.declare_parameter("final_only", True)
        self.declare_parameter("publish_errors_as_text", True)

        self.input_topic = str(self.get_parameter("input_topic").value)
        self.output_topic = str(self.get_parameter("output_topic").value)
        self.final_only = _as_bool(self.get_parameter("final_only").value)
        self.publish_errors_as_text = _as_bool(self.get_parameter("publish_errors_as_text").value)

        latched_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.publisher = self.create_publisher(String, self.output_topic, latched_qos)
        self.subscription = self.create_subscription(
            AsrResult,
            self.input_topic,
            self._on_result,
            latched_qos,
        )
        self.get_logger().info(
            "Text output node started: "
            f"{self.input_topic} -> {self.output_topic}, final_only={self.final_only}"
        )

    def _on_result(self, msg: AsrResult) -> None:
        """Relay final transcription as plain text message."""
        if self.final_only and not bool(msg.is_final):
            return

        if msg.success and msg.text.strip():
            payload = msg.text.strip()
        elif self.publish_errors_as_text and not msg.success:
            payload = f"[{msg.backend}] ERROR {msg.error_code}: {msg.error_message}".strip()
        else:
            return

        out = String()
        out.data = payload
        self.publisher.publish(out)


def main() -> None:
    rclpy.init()
    node = AsrTextOutputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
