from __future__ import annotations

from pathlib import Path

from web_gui.app.noise_service import apply_noise_levels


def test_apply_noise_levels_generates_files() -> None:
    generated = apply_noise_levels("data/sample/en_hello.wav", [20.0, 10.0])
    assert len(generated) == 2
    for path in generated:
        assert Path(path).exists()
