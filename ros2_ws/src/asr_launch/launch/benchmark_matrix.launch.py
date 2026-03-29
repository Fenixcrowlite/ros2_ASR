"""Benchmark manager launch for provider-matrix experiments.

Expected behavior:
- starts benchmark manager node
- intended for multi-provider benchmark matrix controlled via action goals
"""

from asr_launch.launch_env import runtime_python_env
from asr_launch.launch_guard import assert_no_conflicting_managed_stack
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    assert_no_conflicting_managed_stack()
    configs_root = DeclareLaunchArgument("configs_root", default_value="configs")
    artifacts_root = DeclareLaunchArgument("artifacts_root", default_value="artifacts")
    node_env = runtime_python_env()

    benchmark_node = Node(
        package="asr_benchmark_nodes",
        executable="benchmark_manager_node",
        name="benchmark_manager_node",
        output="screen",
        additional_env=node_env,
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
