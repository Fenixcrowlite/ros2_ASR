"""Streaming-focused runtime launch.

Expected behavior:
- starts runtime pipeline with microphone/stream-like chunk settings
- enables lower VAD silence window for near-real-time segmentation
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    runtime_profile = DeclareLaunchArgument("runtime_profile", default_value="default_runtime")
    provider_profile = DeclareLaunchArgument("provider_profile", default_value="providers/whisper_local")
    input_mode = DeclareLaunchArgument("input_mode", default_value="mic")

    audio_input = Node(
        package="asr_runtime_nodes",
        executable="audio_input_node",
        name="audio_input_node",
        output="screen",
        parameters=[
            {"input_mode": LaunchConfiguration("input_mode")},
            {"chunk_ms": 300},
            {"mic_capture_sec": 8.0},
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
        parameters=[
            {"energy_threshold": 450},
            {"max_silence_ms": 500},
            {"min_segment_ms": 250},
        ],
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
        input_mode,
        audio_input,
        audio_preprocess,
        vad_segmenter,
        orchestrator,
    ])
