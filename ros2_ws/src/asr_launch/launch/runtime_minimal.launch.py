"""Minimal runtime pipeline launch.

Expected behavior:
- starts audio input (file mode), preprocess, VAD, and orchestrator nodes
- resolves runtime/provider profiles for orchestrator
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    runtime_profile = DeclareLaunchArgument("runtime_profile", default_value="default_runtime")
    provider_profile = DeclareLaunchArgument("provider_profile", default_value="providers/whisper_local")
    namespace = DeclareLaunchArgument("namespace", default_value="/asr")

    audio_input = Node(
        package="asr_runtime_nodes",
        executable="audio_input_node",
        name="audio_input_node",
        output="screen",
        parameters=[
            {"input_mode": "file"},
            {"file_path": "data/sample/vosk_test.wav"},
            {"chunk_ms": 500},
        ],
    )

    audio_preprocess = Node(
        package="asr_runtime_nodes",
        executable="audio_preprocess_node",
        name="audio_preprocess_node",
        output="screen",
    )

    vad_segmenter = Node(
        package="asr_runtime_nodes",
        executable="vad_segmenter_node",
        name="vad_segmenter_node",
        output="screen",
    )

    orchestrator = Node(
        package="asr_runtime_nodes",
        executable="asr_orchestrator_node",
        name="asr_orchestrator_node",
        output="screen",
        parameters=[
            {"runtime_profile": LaunchConfiguration("runtime_profile")},
            {"provider_profile": LaunchConfiguration("provider_profile")},
        ],
    )

    return LaunchDescription([
        runtime_profile,
        provider_profile,
        namespace,
        audio_input,
        audio_preprocess,
        vad_segmenter,
        orchestrator,
    ])
