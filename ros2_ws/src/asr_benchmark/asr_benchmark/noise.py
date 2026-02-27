from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def add_white_noise_snr(input_wav: str, output_wav: str, snr_db: float, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    with wave.open(input_wav, "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    signal = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    if signal.size == 0:
        Path(output_wav).write_bytes(Path(input_wav).read_bytes())
        return

    signal_power = np.mean(signal**2)
    noise_power = signal_power / (10 ** (snr_db / 10.0))
    noise = rng.normal(0.0, np.sqrt(noise_power), size=signal.shape)
    mixed = np.clip(signal + noise, -32768, 32767).astype(np.int16)

    with wave.open(output_wav, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(mixed.tobytes())
