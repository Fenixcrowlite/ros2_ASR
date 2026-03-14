"""Gateway + runtime launch.

Expected behavior:
- starts runtime pipeline nodes
- starts FastAPI gateway server for GUI/backend API access
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    runtime_profile = DeclareLaunchArgument("runtime_profile", default_value="default_runtime")
    provider_profile = DeclareLaunchArgument("provider_profile", default_value="providers/whisper_local")
    gateway_host = DeclareLaunchArgument("gateway_host", default_value="0.0.0.0")
    gateway_port = DeclareLaunchArgument("gateway_port", default_value="8088")

    nodes = [
        Node(
            package="asr_runtime_nodes",
            executable="audio_input_node",
            name="audio_input_node",
            output="screen",
            parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
        ),
        Node(
            package="asr_runtime_nodes",
            executable="audio_preprocess_node",
            name="audio_preprocess_node",
            output="screen",
            parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
        ),
        Node(
            package="asr_runtime_nodes",
            executable="vad_segmenter_node",
            name="vad_segmenter_node",
            output="screen",
            parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
        ),
        Node(
            package="asr_runtime_nodes",
            executable="asr_orchestrator_node",
            name="asr_orchestrator_node",
            output="screen",
            parameters=[
                {"runtime_profile": LaunchConfiguration("runtime_profile")},
                {"provider_profile": LaunchConfiguration("provider_profile")},
            ],
        ),
        Node(
            package="asr_gateway",
            executable="asr_gateway_server",
            name="asr_gateway_server",
            output="screen",
            additional_env={
                "ASR_GATEWAY_HOST": LaunchConfiguration("gateway_host"),
                "ASR_GATEWAY_PORT": LaunchConfiguration("gateway_port"),
            },
        ),
    ]

    return LaunchDescription([
        runtime_profile,
        provider_profile,
        gateway_host,
        gateway_port,
        *nodes,
    ])
