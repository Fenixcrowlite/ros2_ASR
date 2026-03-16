"""Deterministic benchmark noise augmentation utilities."""

from __future__ import annotations

import audioop
import random
import wave
from array import array
from pathlib import Path
from typing import Any


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

    pcm16 = raw_frames if params.sampwidth == 2 else audioop.lin2lin(raw_frames, params.sampwidth, 2)
    signal_rms = max(audioop.rms(pcm16, 2), 1)
    target_noise_rms = max(int(signal_rms / (10 ** (float(snr_db) / 20.0))), 1)

    rng = random.Random(seed)
    samples = array("h")
    samples.frombytes(pcm16)

    noise_samples = array("h")
    clip = 32767
    for _ in range(len(samples)):
        noise_val = int(rng.gauss(0.0, target_noise_rms / 1.5))
        noise_val = max(-clip, min(clip, noise_val))
        noise_samples.append(noise_val)

    mixed = audioop.add(pcm16, noise_samples.tobytes(), 2)
    encoded = mixed if params.sampwidth == 2 else audioop.lin2lin(mixed, 2, params.sampwidth)

    with wave.open(str(target), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(encoded)

    return str(target)
