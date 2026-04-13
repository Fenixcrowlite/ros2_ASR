"""Deterministic benchmark noise augmentation utilities."""

from __future__ import annotations

import math
import random
import shutil
import wave
from pathlib import Path
from typing import Any

from asr_core.audio import pcm_decode_samples, pcm_encode_samples

NOISE_LEVELS: tuple[dict[str, Any], ...] = (
    {
        "id": "clean",
        "label": "Clean",
        "snr_db": None,
        "description": "Reference baseline without synthetic corruption.",
    },
    {
        "id": "light",
        "label": "Light",
        "snr_db": 30.0,
        "description": "Barely audible additive noise for mild robustness drift checks.",
    },
    {
        "id": "medium",
        "label": "Medium",
        "snr_db": 20.0,
        "description": "Moderate background interference representative of common ambient noise.",
    },
    {
        "id": "heavy",
        "label": "Heavy",
        "snr_db": 10.0,
        "description": "Aggressive corruption that starts to stress decoding and VAD.",
    },
    {
        "id": "extreme",
        "label": "Extreme",
        "snr_db": 0.0,
        "description": "Speech and noise energy are roughly equal; useful as a failure boundary.",
    },
)

NOISE_LEVELS_DB = {str(item["id"]): item["snr_db"] for item in NOISE_LEVELS}
NOISE_LEVEL_ORDER = tuple(str(item["id"]) for item in NOISE_LEVELS)

NOISE_MODES: tuple[dict[str, Any], ...] = (
    {
        "id": "white",
        "label": "White Noise",
        "family": "stationary",
        "description": "Broadband Gaussian baseline used for simple additive SNR sweeps.",
    },
    {
        "id": "pink",
        "label": "Pink Noise",
        "family": "colored",
        "description": "1/f-tilted noise that better matches many natural and room-like spectra.",
    },
    {
        "id": "brown",
        "label": "Brown Noise",
        "family": "colored",
        "description": "Low-frequency-heavy rumble that stresses endpointing and low-band robustness.",
    },
    {
        "id": "babble",
        "label": "Babble",
        "family": "speech_like",
        "description": "Synthetic multi-speaker interference with syllabic amplitude modulation.",
    },
    {
        "id": "hum",
        "label": "Hum",
        "family": "tonal",
        "description": "Mains-like hum plus harmonics and light hiss for tonal background stress.",
    },
)

NOISE_MODES_DB = {str(item["id"]): item for item in NOISE_MODES}

SCENARIO_ALIASES = {
    "noise_robustness_placeholder": "noise_robustness",
}

SCENARIO_NOISE_DEFAULTS: dict[str, dict[str, Any]] = {
    "clean_baseline": {
        "mode": "white",
        "levels": ["clean"],
    },
    "noise_robustness": {
        "mode": "white",
        "levels": ["clean", "light", "medium", "heavy"],
    },
    "provider_comparison": {
        "mode": "white",
        "levels": ["clean"],
    },
    "latency_profile": {
        "mode": "white",
        "levels": ["clean"],
    },
}


def canonicalize_scenario_name(scenario: str) -> str:
    name = str(scenario or "").strip() or "clean_baseline"
    return str(SCENARIO_ALIASES.get(name, name))


def noise_catalog() -> dict[str, Any]:
    return {
        "levels": [dict(item) for item in NOISE_LEVELS],
        "modes": [dict(item) for item in NOISE_MODES],
        "scenario_defaults": {
            key: {
                "mode": str(value.get("mode", "white") or "white"),
                "levels": [str(item) for item in value.get("levels", []) if str(item).strip()],
            }
            for key, value in SCENARIO_NOISE_DEFAULTS.items()
        },
        "aliases": dict(SCENARIO_ALIASES),
    }


def _normalize_noise_levels(raw_levels: Any) -> list[str]:
    explicit_levels = raw_levels
    if isinstance(explicit_levels, str):
        explicit_levels = [item.strip() for item in explicit_levels.split(",") if item.strip()]
    if not isinstance(explicit_levels, list):
        explicit_levels = []

    normalized: list[str] = []
    for item in explicit_levels:
        level = str(item or "").strip().lower()
        if not level:
            continue
        if level not in NOISE_LEVELS_DB:
            raise ValueError(
                "Unsupported noise level: "
                f"{level}. Supported levels: {', '.join(NOISE_LEVEL_ORDER)}"
            )
        if level not in normalized:
            normalized.append(level)
    return normalized


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

    scenario_name = canonicalize_scenario_name(scenario)
    if not str(scenario or "").strip() and profile_scenarios:
        for profile_scenario in profile_scenarios:
            candidate = canonicalize_scenario_name(str(profile_scenario or "").strip())
            if candidate:
                scenario_name = candidate
                break

    selected_levels = _normalize_noise_levels(noise_cfg.get("levels", []))
    scenario_defaults = SCENARIO_NOISE_DEFAULTS.get(
        scenario_name, SCENARIO_NOISE_DEFAULTS["clean_baseline"]
    )
    if not selected_levels:
        selected_levels = list(scenario_defaults.get("levels", ["clean"]))

    mode = str(
        noise_cfg.get("mode", scenario_defaults.get("mode", "white")) or scenario_defaults.get("mode", "white")
    ).strip().lower()
    if mode in {"", "none"}:
        mode = str(scenario_defaults.get("mode", "white") or "white")
    if mode not in NOISE_MODES_DB:
        raise ValueError(
            "Unsupported noise mode: "
            f"{mode}. Supported modes: {', '.join(sorted(NOISE_MODES_DB))}"
        )

    seed = int(noise_cfg.get("seed", 1337) or 1337)
    plans: list[dict[str, Any]] = []
    for level in selected_levels:
        snr_db = NOISE_LEVELS_DB.get(level)
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


def _rms(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(float(value) * float(value) for value in values) / float(len(values)))


def _zero_center(values: list[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / float(len(values))
    return [value - mean for value in values]


def _scale_to_target_rms(values: list[float], *, target_rms: float) -> list[float]:
    if not values:
        return []
    current_rms = _rms(values)
    if current_rms <= 0.0 or target_rms <= 0.0:
        return [0.0 for _ in values]
    gain = float(target_rms) / float(current_rms)
    return [value * gain for value in values]


def _limit_peak(values: list[float], *, limit: float) -> list[float]:
    if not values:
        return []
    peak = max(abs(value) for value in values) or 0.0
    if peak <= 0.0 or peak <= limit:
        return values
    gain = float(limit) / float(peak)
    return [value * gain for value in values]


def _generate_white_noise(frame_count: int, *, rng: random.Random) -> list[float]:
    return [rng.gauss(0.0, 1.0) for _ in range(frame_count)]


def _generate_pink_noise(frame_count: int, *, rng: random.Random) -> list[float]:
    b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
    out: list[float] = []
    for _ in range(frame_count):
        white = rng.gauss(0.0, 1.0)
        b0 = (0.99886 * b0) + (white * 0.0555179)
        b1 = (0.99332 * b1) + (white * 0.0750759)
        b2 = (0.96900 * b2) + (white * 0.1538520)
        b3 = (0.86650 * b3) + (white * 0.3104856)
        b4 = (0.55000 * b4) + (white * 0.5329522)
        b5 = (-0.7616 * b5) - (white * 0.0168980)
        pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + (white * 0.5362)
        b6 = white * 0.115926
        out.append(pink)
    return out


def _generate_brown_noise(frame_count: int, *, rng: random.Random) -> list[float]:
    state = 0.0
    out: list[float] = []
    for _ in range(frame_count):
        state = (state * 0.985) + (rng.gauss(0.0, 1.0) * 0.12)
        out.append(state)
    return out


def _generate_syllabic_envelope(
    frame_count: int,
    *,
    sample_rate_hz: int,
    rng: random.Random,
) -> list[float]:
    min_segment = max(int(sample_rate_hz * 0.04), 1)
    max_segment = max(int(sample_rate_hz * 0.22), min_segment + 1)
    current = rng.uniform(0.0, 0.35)
    remaining = 0
    step = 0.0
    envelope: list[float] = []
    while len(envelope) < frame_count:
        if remaining <= 0:
            segment_len = rng.randint(min_segment, max_segment)
            target = rng.uniform(0.0, 0.08) if rng.random() < 0.18 else rng.uniform(0.25, 1.0)
            step = (target - current) / float(segment_len)
            remaining = segment_len
        current += step
        remaining -= 1
        envelope.append(max(0.0, current))
    return envelope[:frame_count]


def _generate_babble_noise(
    frame_count: int,
    *,
    sample_rate_hz: int,
    rng: random.Random,
) -> list[float]:
    speaker_count = 6
    babble = [0.0 for _ in range(frame_count)]
    for _ in range(speaker_count):
        base = _generate_pink_noise(frame_count, rng=rng)
        envelope = _generate_syllabic_envelope(
            frame_count,
            sample_rate_hz=sample_rate_hz,
            rng=rng,
        )
        voicing_hz = rng.uniform(85.0, 260.0)
        voicing_phase = rng.uniform(0.0, math.tau)
        breathiness = rng.uniform(0.35, 0.65)
        for index in range(frame_count):
            time_sec = index / float(sample_rate_hz)
            voicing = breathiness + ((1.0 - breathiness) * abs(
                math.sin((math.tau * voicing_hz * time_sec) + voicing_phase)
            ))
            babble[index] += base[index] * envelope[index] * voicing
    return babble


def _generate_hum_noise(
    frame_count: int,
    *,
    sample_rate_hz: int,
    rng: random.Random,
) -> list[float]:
    base_hz = 50.0
    harmonic_weights = (
        (1.0, base_hz),
        (0.45, base_hz * 2.0),
        (0.18, base_hz * 3.0),
        (0.08, base_hz * 4.0),
    )
    phases = [rng.uniform(0.0, math.tau) for _ in harmonic_weights]
    hiss = _generate_white_noise(frame_count, rng=rng)
    modulation_phase = rng.uniform(0.0, math.tau)
    out: list[float] = []
    for index in range(frame_count):
        time_sec = index / float(sample_rate_hz)
        harmonic = sum(
            weight * math.sin((math.tau * frequency * time_sec) + phase)
            for (weight, frequency), phase in zip(harmonic_weights, phases)
        )
        modulation = 0.88 + (0.12 * math.sin((math.tau * 0.35 * time_sec) + modulation_phase))
        out.append((harmonic * modulation) + (0.12 * hiss[index]))
    return out


def _generate_noise_frames(
    *,
    frame_count: int,
    sample_rate_hz: int,
    mode: str,
    rng: random.Random,
) -> list[float]:
    if frame_count <= 0:
        return []
    if mode == "white":
        return _generate_white_noise(frame_count, rng=rng)
    if mode == "pink":
        return _generate_pink_noise(frame_count, rng=rng)
    if mode == "brown":
        return _generate_brown_noise(frame_count, rng=rng)
    if mode == "babble":
        return _generate_babble_noise(frame_count, sample_rate_hz=sample_rate_hz, rng=rng)
    if mode == "hum":
        return _generate_hum_noise(frame_count, sample_rate_hz=sample_rate_hz, rng=rng)
    raise ValueError(
        f"Unsupported noise mode: {mode}. Supported modes: {', '.join(sorted(NOISE_MODES_DB))}"
    )


def _expand_frames_to_channels(values: list[float], *, channels: int) -> list[float]:
    if channels <= 1:
        return list(values)
    expanded: list[float] = []
    for value in values:
        for _ in range(channels):
            expanded.append(value)
    return expanded


def apply_noise_to_wav(
    *,
    source_path: str,
    output_path: str,
    snr_db: float,
    seed: int,
    noise_mode: str = "white",
) -> str:
    source = Path(source_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    mode = str(noise_mode or "white").strip().lower()
    if mode in {"none", "clean"}:
        shutil.copyfile(source, target)
        return str(target)
    if mode not in NOISE_MODES_DB:
        raise ValueError(
            f"Unsupported noise mode: {mode}. Supported modes: {', '.join(sorted(NOISE_MODES_DB))}"
        )

    with wave.open(str(source), "rb") as reader:
        params = reader.getparams()
        raw_frames = reader.readframes(reader.getnframes())

    if params.sampwidth <= 0:
        raise ValueError(f"Unsupported sample width: {params.sampwidth}")
    if params.nchannels <= 0:
        raise ValueError(f"Unsupported channel count: {params.nchannels}")

    signed = params.sampwidth != 1
    samples = pcm_decode_samples(raw_frames, sample_width=params.sampwidth, signed=signed)
    if not samples:
        raise ValueError("Source WAV does not contain PCM frames")

    usable = len(samples) - (len(samples) % params.nchannels)
    if usable <= 0:
        raise ValueError("Source WAV does not contain complete PCM frames")
    signal_samples = samples[:usable]
    frame_count = usable // params.nchannels

    signal_rms = max(_rms(signal_samples), 1.0)
    target_noise_rms = max(signal_rms / (10 ** (float(snr_db) / 20.0)), 1.0)

    rng = random.Random(seed)  # nosec B311
    frame_noise = _generate_noise_frames(
        frame_count=frame_count,
        sample_rate_hz=max(int(params.framerate or 16000), 1),
        mode=mode,
        rng=rng,
    )
    centered_noise = _zero_center(frame_noise)
    scaled_noise = _scale_to_target_rms(centered_noise, target_rms=target_noise_rms)
    noise_samples = _expand_frames_to_channels(scaled_noise, channels=params.nchannels)

    clip_limit = (1 << ((params.sampwidth * 8) - 1)) - 1 if signed else 127
    mixed = [signal_samples[index] + noise_samples[index] for index in range(len(signal_samples))]
    mixed = _limit_peak(mixed, limit=float(clip_limit) * 0.985)
    encoded = pcm_encode_samples(mixed, sample_width=params.sampwidth, signed=signed)

    with wave.open(str(target), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(encoded)

    return str(target)
