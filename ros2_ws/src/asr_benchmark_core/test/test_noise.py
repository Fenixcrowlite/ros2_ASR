"""Unit tests for benchmark noise catalog and augmentation helpers."""

from __future__ import annotations

import math
import tempfile
import unittest
import wave
from pathlib import Path

from asr_benchmark_core.noise import (
    apply_noise_to_wav,
    noise_catalog,
    resolve_noise_plan,
)
from asr_core.audio import pcm_encode_samples


def _write_test_wav(path: Path, *, frames: int = 4000, sample_rate_hz: int = 16000) -> None:
    samples = [
        int(9000 * math.sin((2.0 * math.pi * 440.0 * index) / float(sample_rate_hz)))
        for index in range(frames)
    ]
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate_hz)
        writer.writeframes(pcm_encode_samples(samples, sample_width=2, signed=True))


class NoiseCatalogTest(unittest.TestCase):
    def test_noise_catalog_contains_modes_levels_and_scenario_defaults(self) -> None:
        catalog = noise_catalog()
        self.assertIn("levels", catalog)
        self.assertIn("modes", catalog)
        self.assertIn("scenario_defaults", catalog)
        self.assertTrue(any(item["id"] == "babble" for item in catalog["modes"]))
        self.assertTrue(any(item["id"] == "extreme" for item in catalog["levels"]))
        self.assertEqual(
            catalog["scenario_defaults"]["noise_robustness"]["levels"],
            ["clean", "light", "medium", "heavy"],
        )

    def test_resolve_noise_plan_uses_noise_robustness_defaults(self) -> None:
        plan = resolve_noise_plan(
            scenario="noise_robustness",
            benchmark_settings={"noise": {"mode": "pink"}},
        )
        self.assertEqual(
            [item["noise_level"] for item in plan],
            ["clean", "light", "medium", "heavy"],
        )
        self.assertEqual([item["noise_mode"] for item in plan], ["none", "pink", "pink", "pink"])

    def test_resolve_noise_plan_accepts_legacy_placeholder_alias(self) -> None:
        plan = resolve_noise_plan(
            scenario="noise_robustness_placeholder",
            benchmark_settings={"noise": {"levels": ["light"], "mode": "babble"}},
        )
        self.assertEqual(plan[0]["scenario"], "noise_robustness")
        self.assertEqual(plan[0]["noise_level"], "light")
        self.assertEqual(plan[0]["noise_mode"], "babble")

    def test_resolve_noise_plan_supports_custom_snr_db_variants(self) -> None:
        plan = resolve_noise_plan(
            scenario="noise_robustness",
            benchmark_settings={
                "noise": {
                    "mode": "pink",
                    "levels": ["clean", "light"],
                    "custom_snr_db": [17.5, 5.0],
                }
            },
        )
        self.assertEqual(
            [item["noise_level"] for item in plan],
            ["clean", "light", "custom_17p5db", "custom_5db"],
        )
        self.assertEqual(
            [item["noise_origin"] for item in plan],
            ["preset", "preset", "custom", "custom"],
        )
        self.assertEqual([item["snr_db"] for item in plan], [None, 30.0, 17.5, 5.0])


class NoiseApplyTest(unittest.TestCase):
    def test_apply_noise_to_wav_supports_multiple_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source = tmp_path / "source.wav"
            _write_test_wav(source)
            source_bytes = source.read_bytes()

            for mode in ("white", "pink", "brown", "babble", "hum"):
                output = tmp_path / f"{mode}.wav"
                apply_noise_to_wav(
                    source_path=str(source),
                    output_path=str(output),
                    snr_db=15.0,
                    seed=1234,
                    noise_mode=mode,
                )
                self.assertTrue(output.exists(), mode)
                self.assertNotEqual(output.read_bytes(), source_bytes, mode)

    def test_apply_noise_to_wav_copies_clean_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source = tmp_path / "source.wav"
            output = tmp_path / "copy.wav"
            _write_test_wav(source)

            apply_noise_to_wav(
                source_path=str(source),
                output_path=str(output),
                snr_db=30.0,
                seed=1337,
                noise_mode="none",
            )
            self.assertEqual(output.read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
