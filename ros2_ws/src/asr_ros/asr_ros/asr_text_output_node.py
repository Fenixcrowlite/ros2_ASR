"""Dedicated text output node.

Subscribes to structured ASR results and republishes plain text into a separate topic.
"""

from __future__ import annotations

import rclpy
from asr_core.ros_parameters import parameter_bool, parameter_string
from asr_interfaces.msg import AsrResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from asr_ros.shutdown import safe_shutdown_node


def _as_bool(value: object) -> bool:
    """Parse ROS parameter value that can be bool/string."""
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class AsrTextOutputNode(Node):
    """Relay structured ASR results into a plain-text topic.

    Published topics:
    - `output_topic` (`std_msgs/String`, default `/asr/text/plain`)

    Subscribed topics:
    - `input_topic` (`asr_interfaces/AsrResult`, default `/asr/text`)

    Parameters:
    - `input_topic`
    - `output_topic`
    - `final_only`
    - `publish_errors_as_text`
    """

    def __init__(self) -> None:
        super().__init__("asr_text_output_node")
        self.declare_parameter("input_topic", "/asr/text")
        self.declare_parameter("output_topic", "/asr/text/plain")
        self.declare_parameter("final_only", True)
        self.declare_parameter("publish_errors_as_text", True)

        self.input_topic = parameter_string(self, "input_topic")
        self.output_topic = parameter_string(self, "output_topic")
        self.final_only = _as_bool(parameter_bool(self, "final_only", default=True))
        self.publish_errors_as_text = _as_bool(
            parameter_bool(self, "publish_errors_as_text", default=True)
        )

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
    """Start the legacy text relay node."""
    rclpy.init()
    node = AsrTextOutputNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        safe_shutdown_node(node=node, rclpy_module=rclpy)


if __name__ == "__main__":
    main()
