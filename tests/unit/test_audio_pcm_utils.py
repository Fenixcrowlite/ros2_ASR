from __future__ import annotations

from asr_core.audio import (
    pcm_decode_samples,
    pcm_encode_samples,
    pcm_max_abs,
    pcm_resample_linear,
    pcm_rms,
    pcm_scale,
    pcm_signed_from_encoding,
    pcm_to_mono,
)


def test_pcm_u8_roundtrip_and_rms() -> None:
    payload = bytes([0, 128, 255])

    samples = pcm_decode_samples(payload, sample_width=1, signed=False)

    assert samples == [-128, 0, 127]
    assert pcm_encode_samples(samples, sample_width=1, signed=False) == payload
    assert round(pcm_rms(payload, sample_width=1, signed=False), 3) == 104.104


def test_pcm_to_mono_averages_stereo_pairs() -> None:
    stereo = pcm_encode_samples([1000, -1000, 2000, -2000], sample_width=2, signed=True)

    mono = pcm_to_mono(stereo, sample_width=2, channels=2, signed=True)

    assert pcm_decode_samples(mono, sample_width=2, signed=True) == [0, 0]


def test_pcm_resample_linear_preserves_shape_for_simple_ramp() -> None:
    source = pcm_encode_samples([0, 1000, 2000, 3000], sample_width=2, signed=True)

    resampled = pcm_resample_linear(
        source,
        sample_width=2,
        channels=1,
        source_rate_hz=4,
        target_rate_hz=8,
        signed=True,
    )

    decoded = pcm_decode_samples(resampled, sample_width=2, signed=True)
    assert len(decoded) == 8
    assert decoded[0] == 0
    assert decoded[-1] == 3000
    assert decoded[3] >= decoded[2]


def test_pcm_scale_and_max_abs() -> None:
    source = pcm_encode_samples([1000, -2000, 3000], sample_width=2, signed=True)

    scaled = pcm_scale(source, sample_width=2, factor=0.5, signed=True)

    assert pcm_decode_samples(scaled, sample_width=2, signed=True) == [500, -1000, 1500]
    assert pcm_max_abs(source, sample_width=2, signed=True) == 3000


def test_pcm_signed_from_encoding_distinguishes_u8() -> None:
    assert pcm_signed_from_encoding("pcm_u8", default=True) is False
    assert pcm_signed_from_encoding("pcm_s16le", default=False) is True
