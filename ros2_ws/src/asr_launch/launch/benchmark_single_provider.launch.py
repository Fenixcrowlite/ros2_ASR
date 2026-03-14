"""Benchmark manager launch for single-provider experiments.

Expected behavior:
- starts benchmark manager node exposing actions/services
- suitable for one-provider benchmark job execution from CLI/gateway
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    configs_root = DeclareLaunchArgument("configs_root", default_value="configs")
    artifacts_root = DeclareLaunchArgument("artifacts_root", default_value="artifacts")

    benchmark_node = Node(
        package="asr_benchmark_nodes",
        executable="benchmark_manager_node",
        name="benchmark_manager_node",
        output="screen",
        parameters=[
            {"configs_root": LaunchConfiguration("configs_root")},
            {"artifacts_root": LaunchConfiguration("artifacts_root")},
        ],
    )

    return LaunchDescription([
        configs_root,
        artifacts_root,
        benchmark_node,
    ])
