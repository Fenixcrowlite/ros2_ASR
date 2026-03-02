"""Option catalogs for Web GUI forms."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from web_gui.app.paths import PROFILES_DIR, REPO_ROOT

LANGUAGES = [
    "en-US",
    "ru-RU",
    "sk-SK",
    "cs-CZ",
    "pl-PL",
    "de-DE",
    "fr-FR",
    "es-ES",
    "it-IT",
    "pt-PT",
    "uk-UA",
    "tr-TR",
    "ja-JP",
    "ko-KR",
    "zh-CN",
]

BACKEND_MODEL_PRESETS = {
    "mock": ["deterministic"],
    "whisper": ["tiny", "base", "small", "medium", "large-v3"],
    "vosk": ["vosk-model-small-en-us-0.15", "vosk-model-ru-0.42"],
    "google": ["latest_short", "latest_long", "chirp_2"],
    "aws": ["transcribe"],
    "azure": ["speech"],
}

METRIC_KEYS = [
    "wer",
    "cer",
    "latency_ms",
    "rtf",
    "cpu_percent",
    "ram_mb",
    "gpu_util_percent",
    "gpu_mem_mb",
    "cost_estimate",
    "success_rate",
]

INTERFACE_OPTIONS = ["core", "ros_service", "ros_action"]
BACKEND_OPTIONS = ["mock", "vosk", "whisper", "google", "aws", "azure"]
SCENARIO_OPTIONS = ["clean", "snr30", "snr20", "snr10", "snr0"]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def list_profiles() -> list[str]:
    """Return list of saved GUI profile names."""
    if not PROFILES_DIR.exists():
        return []
    names = [item.stem for item in PROFILES_DIR.glob("*.yaml")]
    return sorted(set(names))


def get_options_payload() -> dict[str, Any]:
    """Build option payload consumed by frontend."""
    default_cfg = _load_yaml(REPO_ROOT / "configs" / "default.yaml")
    live_cfg = _load_yaml(REPO_ROOT / "configs" / "live_mic_whisper.yaml")

    return {
        "languages": LANGUAGES,
        "interfaces": INTERFACE_OPTIONS,
        "backends": BACKEND_OPTIONS,
        "backend_models": BACKEND_MODEL_PRESETS,
        "metrics": METRIC_KEYS,
        "benchmark_scenarios": SCENARIO_OPTIONS,
        "base_configs": [
            "configs/default.yaml",
            "configs/live_mic_whisper.yaml",
        ],
        "profiles": list_profiles(),
        "defaults": {
            "default": default_cfg,
            "live_mic_whisper": live_cfg,
        },
    }
