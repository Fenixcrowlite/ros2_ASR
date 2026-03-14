from setuptools import find_packages, setup

package_name = "asr_launch"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md", "TODO.md"]),
        (
            f"share/{package_name}/launch",
            [
                "launch/runtime_minimal.launch.py",
                "launch/runtime_streaming.launch.py",
                "launch/benchmark_single_provider.launch.py",
                "launch/benchmark_matrix.launch.py",
                "launch/gateway_with_runtime.launch.py",
                "launch/full_stack_dev.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="maintainer@example.com",
    description="Launch scenarios for runtime, benchmark, gateway and full stack",
    license="MIT",
)
