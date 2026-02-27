from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config_arg = DeclareLaunchArgument("config", default_value="configs/default.yaml")
    dataset_arg = DeclareLaunchArgument(
        "dataset", default_value="data/transcripts/sample_manifest.csv"
    )

    node = Node(
        package="asr_benchmark",
        executable="asr_benchmark_node",
        output="screen",
        parameters=[
            {"config": LaunchConfiguration("config")},
            {"dataset": LaunchConfiguration("dataset")},
        ],
    )
    return LaunchDescription([config_arg, dataset_arg, node])
