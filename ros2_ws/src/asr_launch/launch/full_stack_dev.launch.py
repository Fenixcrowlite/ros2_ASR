"""Full-stack development launch.

Expected behavior:
- starts runtime + gateway stack
- starts benchmark manager stack
- provides end-to-end local development topology
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir


def generate_launch_description() -> LaunchDescription:
    # "Full stack" means the operator/runtime path plus the benchmark backend
    # used by dataset import, benchmark execution, and results pages.
    runtime_profile = DeclareLaunchArgument("runtime_profile", default_value="default_runtime")
    provider_profile = DeclareLaunchArgument("provider_profile", default_value="providers/whisper_local")
    gateway_host = DeclareLaunchArgument("gateway_host", default_value="127.0.0.1")
    gateway_port = DeclareLaunchArgument("gateway_port", default_value="8088")
    configs_root = DeclareLaunchArgument("configs_root", default_value="configs")
    artifacts_root = DeclareLaunchArgument("artifacts_root", default_value="artifacts")

    # Reuse the smaller launch so there is one canonical definition of the
    # runtime+gateway topology.
    runtime_and_gateway = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ThisLaunchFileDir(), "/gateway_with_runtime.launch.py"]),
        launch_arguments={
            "runtime_profile": LaunchConfiguration("runtime_profile"),
            "provider_profile": LaunchConfiguration("provider_profile"),
            "gateway_host": LaunchConfiguration("gateway_host"),
            "gateway_port": LaunchConfiguration("gateway_port"),
        }.items(),
    )
    # Benchmark manager is separate because long-running experiments should not
    # be entangled with the low-latency runtime pipeline.
    benchmark = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([ThisLaunchFileDir(), "/benchmark_matrix.launch.py"]),
        launch_arguments={
            "configs_root": LaunchConfiguration("configs_root"),
            "artifacts_root": LaunchConfiguration("artifacts_root"),
        }.items(),
    )

    return LaunchDescription(
        [
            runtime_profile,
            provider_profile,
            gateway_host,
            gateway_port,
            configs_root,
            artifacts_root,
            runtime_and_gateway,
            benchmark,
        ]
    )
