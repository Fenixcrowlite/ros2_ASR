"""Setuptools entrypoint for the `asr_ros` package."""

from setuptools import find_packages, setup

package_name = "asr_ros"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (
            f"share/{package_name}/launch",
            [
                "launch/bringup.launch.py",
                "launch/demo.launch.py",
                "launch/benchmark.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="asr-team@ros2-asr.localdomain",
    description="ROS2 nodes for ASR services and actions",
    license="MIT",
    entry_points={
        "console_scripts": [
            "asr_server_node = asr_ros.asr_server_node:main",
            "audio_capture_node = asr_ros.audio_capture_node:main",
            "asr_text_output_node = asr_ros.asr_text_output_node:main",
        ],
    },
)
