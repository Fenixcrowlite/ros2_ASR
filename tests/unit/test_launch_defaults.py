from __future__ import annotations

import re
from pathlib import Path


def test_launch_files_default_gateway_host_to_loopback() -> None:
    for rel_path in (
        "ros2_ws/src/asr_launch/launch/gateway_with_runtime.launch.py",
        "ros2_ws/src/asr_launch/launch/full_stack_dev.launch.py",
    ):
        content = Path(rel_path).read_text(encoding="utf-8")
        assert re.search(
            r'DeclareLaunchArgument\("gateway_host", default_value="127\.0\.0\.1"\)',
            content,
        )
