"""ROS launch description for benchmark.launch."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Launch the legacy benchmark node with config and dataset arguments."""
    # Benchmark launch accepts runtime config and dataset manifest path.
    config_arg = DeclareLaunchArgument("config", default_value="configs/default.yaml")
    dataset_arg = DeclareLaunchArgument(
        "dataset", default_value="data/transcripts/sample_manifest.csv"
    )

    benchmark = Node(
        package="asr_benchmark",
        executable="asr_benchmark_node",
        output="screen",
        parameters=[
            {"config": LaunchConfiguration("config")},
            {"dataset": LaunchConfiguration("dataset")},
        ],
    )

    return LaunchDescription([config_arg, dataset_arg, benchmark])
