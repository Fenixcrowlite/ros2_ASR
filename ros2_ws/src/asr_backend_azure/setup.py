from setuptools import find_packages, setup

package_name = "asr_backend_azure"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ASR Team",
    maintainer_email="maintainer@example.com",
    description="Azure backend",
    license="MIT",
    tests_require=["pytest"],
)
