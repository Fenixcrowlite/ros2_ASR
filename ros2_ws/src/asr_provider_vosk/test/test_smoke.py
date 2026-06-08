"""Smoke tests for `asr_provider_vosk` imports and package wiring."""

from __future__ import annotations

import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import_package(self) -> None:
        importlib.import_module("asr_provider_vosk")


if __name__ == "__main__":
    unittest.main()
