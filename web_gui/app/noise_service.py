"""Audio noise augmentation helpers for Web GUI."""

from __future__ import annotations

from pathlib import Path

from asr_benchmark.noise import add_white_noise_snr

from web_gui.app.paths import NOISY_DIR, REPO_ROOT, resolve_under_roots


def apply_noise_levels(source_wav: str, snr_levels: list[float]) -> list[Path]:
    """Create noisy WAV files for each requested SNR level."""
    src = resolve_under_roots(
        source_wav,
        roots=[REPO_ROOT / "data", REPO_ROOT / "web_gui", REPO_ROOT / "results"],
    )
    if src.suffix.lower() != ".wav":
        raise ValueError("Noise overlay requires WAV input")
    if not src.exists():
        raise FileNotFoundError(f"Source WAV not found: {src}")

    NOISY_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for snr in snr_levels:
        snr_label = str(snr).replace(".", "p").replace("-", "m")
        output = NOISY_DIR / f"{src.stem}_snr{snr_label}.wav"
        add_white_noise_snr(str(src), str(output), snr_db=float(snr))
        generated.append(output.resolve())
    return generated
