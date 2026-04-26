"""Unit tests for benchmark configuration validation helpers."""

from __future__ import annotations

import unittest

from asr_config.validation import validate_benchmark_payload


class BenchmarkValidationTest(unittest.TestCase):
    def test_validate_benchmark_payload_accepts_supported_noise_settings(self) -> None:
        payload = {
            "dataset_profile": "datasets/sample_dataset",
            "providers": ["providers/whisper_local"],
            "metric_profiles": ["metrics/default_quality"],
            "execution_mode": "batch",
            "noise": {
                "mode": "babble",
                "levels": ["clean", "light", "medium"],
                "custom_snr_db": [17.5, 5],
                "seed": 1337,
            },
        }
        self.assertEqual(validate_benchmark_payload(payload), [])

    def test_validate_benchmark_payload_rejects_unknown_noise_settings(self) -> None:
        payload = {
            "dataset_profile": "datasets/sample_dataset",
            "providers": ["providers/whisper_local"],
            "metric_profiles": ["metrics/default_quality"],
            "execution_mode": "batch",
            "noise": {
                "mode": "ocean",
                "levels": ["clean", "storm"],
            },
        }
        errors = validate_benchmark_payload(payload)
        self.assertTrue(any("noise.mode" in item for item in errors))
        self.assertTrue(any("noise.levels" in item for item in errors))

    def test_validate_benchmark_payload_rejects_invalid_custom_snr_db(self) -> None:
        payload = {
            "dataset_profile": "datasets/sample_dataset",
            "providers": ["providers/whisper_local"],
            "metric_profiles": ["metrics/default_quality"],
            "execution_mode": "batch",
            "noise": {
                "custom_snr_db": ["abc", 120],
            },
        }
        errors = validate_benchmark_payload(payload)
        self.assertTrue(any("noise.custom_snr_db entries must be numeric" in item for item in errors))
        self.assertTrue(any("noise.custom_snr_db entries must be between -5 and 60 dB" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
