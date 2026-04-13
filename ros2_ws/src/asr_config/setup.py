"""Setuptools entrypoint for the `asr_config` package."""

from setuptools import find_packages, setup

package_name = "asr_config"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="asr-team@ros2-asr.localdomain",
    description="Profile-driven configuration resolver and secret reference model",
    license="MIT",
)
