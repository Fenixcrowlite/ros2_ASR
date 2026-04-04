from setuptools import find_packages, setup

package_name = "asr_runtime_nodes"

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
    description="Runtime pipeline ROS2 nodes (audio input, preprocess, VAD, orchestrator)",
    license="MIT",
    entry_points={
        "console_scripts": [
            "audio_input_node = asr_runtime_nodes.audio_input_node:main",
            "audio_preprocess_node = asr_runtime_nodes.audio_preprocess_node:main",
            "vad_segmenter_node = asr_runtime_nodes.vad_segmenter_node:main",
            "asr_orchestrator_node = asr_runtime_nodes.asr_orchestrator_node:main",
        ]
    },
)
