from __future__ import annotations

from asr_provider_base.catalog import resolve_provider_execution


def test_resolve_provider_execution_merges_preset_and_overrides() -> None:
    payload = {
        "provider_id": "whisper",
        "settings": {
            "model_size": "base",
            "compute_type": "int8",
            "device": "cpu",
            "nested": {"beam_size": 2, "temperature": 0.0},
        },
        "ui": {
            "default_model_preset": "balanced",
            "model_presets": {
                "balanced": {
                    "label": "Balanced",
                    "settings": {"model_size": "base", "nested": {"beam_size": 4}},
                },
                "accurate": {
                    "label": "Accurate",
                    "settings": {"model_size": "small", "nested": {"beam_size": 6}},
                },
            },
        },
    }

    execution = resolve_provider_execution(
        payload,
        preset_id="accurate",
        settings_overrides={"nested": {"temperature": 0.2}, "device": "cuda"},
    )

    assert execution["selected_preset"] == "accurate"
    assert execution["settings"]["model_size"] == "small"
    assert execution["settings"]["device"] == "cuda"
    assert execution["settings"]["nested"]["beam_size"] == 6
    assert execution["settings"]["nested"]["temperature"] == 0.2


def test_resolve_provider_execution_uses_default_preset_when_not_explicit() -> None:
    payload = {
        "provider_id": "google",
        "settings": {"model": "default"},
        "ui": {
            "default_model_preset": "light",
            "model_presets": {
                "light": {"settings": {"model": "latest_short"}},
            },
        },
    }

    execution = resolve_provider_execution(payload)

    assert execution["selected_preset"] == "light"
    assert execution["settings"]["model"] == "latest_short"
