"""Setuptools entrypoint for the `asr_gateway` package."""

from setuptools import find_packages, setup

package_name = "asr_gateway"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
    ],
    install_requires=["setuptools", "fastapi", "uvicorn", "pydantic", "PyYAML"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="asr-team@ros2-asr.localdomain",
    description="Gateway backend between GUI and ROS2/core layers",
    license="MIT",
    entry_points={
        "console_scripts": [
            "asr_gateway_server = asr_gateway.main:main",
        ]
    },
)
