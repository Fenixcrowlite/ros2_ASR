from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    # `config` points to global runtime YAML consumed by asr_server_node.
    config_arg = DeclareLaunchArgument("config", default_value="configs/default.yaml")
    # Audio capture parameters (can override YAML quickly from CLI).
    input_mode_arg = DeclareLaunchArgument("input_mode", default_value="auto")
    wav_path_arg = DeclareLaunchArgument("wav_path", default_value="data/sample/en_hello.wav")
    sample_rate_arg = DeclareLaunchArgument("sample_rate", default_value="16000")
    chunk_ms_arg = DeclareLaunchArgument("chunk_ms", default_value="800")
    device_arg = DeclareLaunchArgument("device", default_value="")
    continuous_arg = DeclareLaunchArgument("continuous", default_value="true")
    mic_capture_sec_arg = DeclareLaunchArgument("mic_capture_sec", default_value="4.0")
    live_enabled_arg = DeclareLaunchArgument("live_stream_enabled", default_value="true")
    live_flush_arg = DeclareLaunchArgument("live_flush_timeout_sec", default_value="1.0")

    # ASR server node: service/action/topics + live chunk subscriber.
    asr_server = Node(
        package="asr_ros",
        executable="asr_server_node",
        name="asr_server_node",
        output="screen",
        parameters=[
            {"config": LaunchConfiguration("config")},
            {"sample_rate": LaunchConfiguration("sample_rate")},
            {"live_stream_enabled": LaunchConfiguration("live_stream_enabled")},
            {"live_flush_timeout_sec": LaunchConfiguration("live_flush_timeout_sec")},
        ],
    )

    # Audio source node: mic or file chunk publisher.
    audio_capture = Node(
        package="asr_ros",
        executable="audio_capture_node",
        name="audio_capture_node",
        output="screen",
        parameters=[
            {"input_mode": LaunchConfiguration("input_mode")},
            {"wav_path": LaunchConfiguration("wav_path")},
            {"sample_rate": LaunchConfiguration("sample_rate")},
            {"chunk_ms": LaunchConfiguration("chunk_ms")},
            {"device": LaunchConfiguration("device")},
            {"continuous": LaunchConfiguration("continuous")},
            {"mic_capture_sec": LaunchConfiguration("mic_capture_sec")},
        ],
    )

    return LaunchDescription(
        [
            config_arg,
            input_mode_arg,
            wav_path_arg,
            sample_rate_arg,
            chunk_ms_arg,
            device_arg,
            continuous_arg,
            mic_capture_sec_arg,
            live_enabled_arg,
            live_flush_arg,
            asr_server,
            audio_capture,
        ]
    )
