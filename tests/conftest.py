from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "ros2_ws" / "src"

for package_root in SRC_ROOT.iterdir():
    if package_root.is_dir():
        sys.path.insert(0, str(package_root))


@pytest.fixture(scope="session")
def sample_wav() -> str:
    return str(ROOT / "data" / "sample" / "en_hello.wav")
