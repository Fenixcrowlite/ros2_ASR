"""Deterministic benchmark noise augmentation utilities."""

from __future__ import annotations

import random
import wave
from pathlib import Path
from typing import Any

from asr_core.audio import pcm_decode_samples, pcm_encode_samples, pcm_rms

NOISE_LEVELS_DB = {
    "clean": None,
    "light": 30.0,
    "medium": 20.0,
    "heavy": 10.0,
    "extreme": 0.0,
}


def resolve_noise_plan(
    *,
    scenario: str,
    benchmark_settings: dict[str, Any] | None = None,
    profile_scenarios: list[str] | None = None,
) -> list[dict[str, Any]]:
    settings = benchmark_settings or {}
    noise_cfg = settings.get("noise", {})
    if not isinstance(noise_cfg, dict):
        noise_cfg = {}

    explicit_levels = noise_cfg.get("levels", [])
    if isinstance(explicit_levels, str):
        explicit_levels = [item.strip() for item in explicit_levels.split(",") if item.strip()]
    if not isinstance(explicit_levels, list):
        explicit_levels = []

    scenario_name = str(scenario or "").strip() or "clean_baseline"
    selected_levels = [str(item) for item in explicit_levels if str(item).strip()]

    if not selected_levels:
        if scenario_name == "noise_robustness":
            selected_levels = ["clean", "light", "medium", "heavy"]
        else:
            selected_levels = ["clean"]

    plans: list[dict[str, Any]] = []
    mode = str(noise_cfg.get("mode", "white")).strip() or "white"
    seed = int(noise_cfg.get("seed", 1337) or 1337)
    for level in selected_levels:
        snr_db = NOISE_LEVELS_DB.get(level)
        if snr_db is None and level != "clean":
            raise ValueError(f"Unsupported noise level: {level}")
        plans.append(
            {
                "scenario": scenario_name,
                "noise_mode": "none" if level == "clean" else mode,
                "noise_level": level,
                "snr_db": snr_db,
                "seed": seed,
            }
        )
    return plans


def apply_noise_to_wav(
    *,
    source_path: str,
    output_path: str,
    snr_db: float,
    seed: int,
) -> str:
    source = Path(source_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(source), "rb") as reader:
        params = reader.getparams()
        raw_frames = reader.readframes(reader.getnframes())

    if params.sampwidth <= 0:
        raise ValueError(f"Unsupported sample width: {params.sampwidth}")

    signed = params.sampwidth != 1
    samples = pcm_decode_samples(raw_frames, sample_width=params.sampwidth, signed=signed)
    if not samples:
        raise ValueError("Source WAV does not contain PCM frames")
    signal_rms = max(pcm_rms(raw_frames, sample_width=params.sampwidth, signed=signed), 1.0)
    target_noise_rms = max(int(signal_rms / (10 ** (float(snr_db) / 20.0))), 1)

    rng = random.Random(seed)  # nosec B311
    clip = (1 << ((params.sampwidth * 8) - 1)) - 1 if signed else 127
    noise_samples: list[int] = []
    for _ in range(len(samples)):
        noise_val = int(rng.gauss(0.0, target_noise_rms / 1.5))
        noise_val = max(-clip, min(clip, noise_val))
        noise_samples.append(noise_val)

    mixed = [sample + noise_samples[index] for index, sample in enumerate(samples)]
    encoded = pcm_encode_samples(mixed, sample_width=params.sampwidth, signed=signed)

    with wave.open(str(target), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(encoded)

    return str(target)
