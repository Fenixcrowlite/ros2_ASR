"""Minimal runtime pipeline launch.

Expected behavior:
- starts audio input (file mode), preprocess, VAD, and orchestrator nodes
- resolves runtime/provider profiles for orchestrator
"""

from asr_launch.launch_env import runtime_python_env
from asr_launch.launch_guard import assert_no_conflicting_managed_stack
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Launch the smallest complete runtime pipeline for file-based operation."""
    assert_no_conflicting_managed_stack()
    runtime_profile = DeclareLaunchArgument("runtime_profile", default_value="default_runtime")
    provider_profile = DeclareLaunchArgument(
        "provider_profile",
        default_value="providers/whisper_local",
    )

    node_env = runtime_python_env()

    audio_input = Node(
        package="asr_runtime_nodes",
        executable="audio_input_node",
        name="audio_input_node",
        output="screen",
        additional_env=node_env,
        parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
    )

    audio_preprocess = Node(
        package="asr_runtime_nodes",
        executable="audio_preprocess_node",
        name="audio_preprocess_node",
        output="screen",
        additional_env=node_env,
        parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
    )

    vad_segmenter = Node(
        package="asr_runtime_nodes",
        executable="vad_segmenter_node",
        name="vad_segmenter_node",
        output="screen",
        additional_env=node_env,
        parameters=[{"runtime_profile": LaunchConfiguration("runtime_profile")}],
    )

    orchestrator = Node(
        package="asr_runtime_nodes",
        executable="asr_orchestrator_node",
        name="asr_orchestrator_node",
        output="screen",
        additional_env=node_env,
        parameters=[
            {"runtime_profile": LaunchConfiguration("runtime_profile")},
            {"provider_profile": LaunchConfiguration("provider_profile")},
        ],
    )

    return LaunchDescription([
        runtime_profile,
        provider_profile,
        audio_input,
        audio_preprocess,
        vad_segmenter,
        orchestrator,
    ])
