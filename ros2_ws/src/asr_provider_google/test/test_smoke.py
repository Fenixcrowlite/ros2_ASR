from __future__ import annotations

import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import_package(self) -> None:
        importlib.import_module("asr_provider_google")


if __name__ == "__main__":
    unittest.main()
