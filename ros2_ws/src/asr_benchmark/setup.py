from setuptools import find_packages, setup

package_name = "asr_benchmark"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/benchmark.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="maintainer@example.com",
    description="ASR benchmark toolkit",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "asr_benchmark_node = asr_benchmark.benchmark_node:main",
            "asr_benchmark_runner = asr_benchmark.runner:main",
        ],
    },
)
