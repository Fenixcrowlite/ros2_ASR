from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    config_arg = DeclareLaunchArgument("config", default_value="configs/default.yaml")
    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("asr_ros"), "launch", "bringup.launch.py"])
        ),
        launch_arguments={"config": LaunchConfiguration("config")}.items(),
    )
    return LaunchDescription([config_arg, bringup])
