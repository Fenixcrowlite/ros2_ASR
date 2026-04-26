"""Legacy ROS2 wrapper node around the compatibility benchmark runner."""

from __future__ import annotations

import rclpy
from asr_core.ros_parameters import parameter_string
from rclpy.node import Node

from asr_benchmark.runner import run_benchmark


class AsrBenchmarkNode(Node):
    """Run the legacy benchmark flow once and exit.

    Published topics:
    - none

    Subscribed topics:
    - none

    Parameters:
    - `config`: runtime config YAML path
    - `dataset`: benchmark manifest path
    - `output_json`: JSON summary output path
    - `output_csv`: CSV summary output path
    - `backends`: comma-separated backend override list
    """

    def __init__(self) -> None:
        super().__init__("asr_benchmark_node")
        self.declare_parameter("config", "configs/default.yaml")
        self.declare_parameter("dataset", "data/transcripts/sample_manifest.csv")
        self.declare_parameter("output_json", "results/benchmark_results.json")
        self.declare_parameter("output_csv", "results/benchmark_results.csv")
        self.declare_parameter("backends", "")

        self._timer = self.create_timer(0.5, self._run_once)
        self._done = False

    def _run_once(self) -> None:
        """Timer callback executing benchmark exactly once."""
        if self._done:
            return
        config = parameter_string(self, "config")
        dataset = parameter_string(self, "dataset")
        output_json = parameter_string(self, "output_json")
        output_csv = parameter_string(self, "output_csv")
        backends_raw = parameter_string(self, "backends")
        backends = (
            [b.strip() for b in backends_raw.split(",") if b.strip()] if backends_raw else None
        )

        self.get_logger().info("Running benchmark")
        records = run_benchmark(
            config_path=config,
            dataset_path=dataset,
            output_json=output_json,
            output_csv=output_csv,
            backends=backends,
        )
        self.get_logger().info(f"Benchmark completed with {len(records)} records")
        self._done = True
        self.destroy_node()


def main() -> None:
    """ROS2 entry point."""
    rclpy.init()
    node = AsrBenchmarkNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.context.ok():
            node.destroy_node()
        if rclpy.ok(context=node.context):
            rclpy.shutdown(context=node.context)


if __name__ == "__main__":
    main()
