"""Option catalogs for Web GUI forms."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from web_gui.app.aws_auth_store import discover_sso_constants, list_auth_profiles
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

LANGUAGE_MODE_OPTIONS = ["config", "manual", "auto"]
INPUT_MODE_OPTIONS = ["auto", "mic", "file"]

SAMPLE_RATE_OPTIONS = [8000, 16000, 22050, 24000, 44100, 48000]
CHUNK_MS_OPTIONS = [200, 400, 800, 1000, 1200]
CHUNK_SEC_OPTIONS = [0.4, 0.6, 0.8, 1.0, 1.2]
RECORD_SEC_OPTIONS = [3.0, 5.0, 8.0, 12.0]
REQUEST_TIMEOUT_OPTIONS = [15.0, 25.0, 40.0, 60.0]
MIC_CAPTURE_SEC_OPTIONS = [2.0, 4.0, 6.0, 8.0]

WHISPER_DEVICE_OPTIONS = ["cpu", "cuda"]
WHISPER_COMPUTE_OPTIONS = ["int8", "int8_float16", "float16", "float32"]

AWS_REGION_OPTIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "eu-north-1",
]
AZURE_REGION_OPTIONS = ["eastus", "westus2", "westeurope", "northeurope"]
GOOGLE_REGION_OPTIONS = ["global", "us", "eu"]

NOISE_LEVEL_PRESETS = ["30,20,10,0", "20,10,0", "15,10,5,0"]
AWS_BUCKET_HINTS = ["my-transcribe-bucket"]
AZURE_ENDPOINT_HINTS = ["optional-endpoint-id"]
AUDIO_DEVICE_HINTS = ["default", "0", "1"]
BENCHMARK_BACKEND_PRESETS = [
    "mock",
    "mock,whisper",
    "mock,whisper,vosk",
    "whisper,google,aws,azure",
    "google,aws,azure",
]
BENCHMARK_SCENARIO_PRESETS = [
    "clean,snr30,snr20,snr10,snr0",
    "clean,snr20,snr10,snr0",
    "clean,snr10,snr0",
]
MODEL_RUN_PRESETS = [
    "mock",
    "mock,whisper:tiny",
    "whisper:tiny,whisper:base,whisper:small",
    "whisper:small,whisper:medium,whisper:large-v3",
    "google:latest_short@global,google:latest_long@global,google:chirp_2@global",
    "whisper:large-v3,google:chirp_2@global,aws:transcribe@us-east-1,azure:speech@eastus",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    if isinstance(payload, dict):
        return payload
    return {}


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({item for item in values if item})


def _discover_base_configs() -> list[str]:
    configs_dir = REPO_ROOT / "configs"
    if not configs_dir.exists():
        return ["configs/default.yaml"]

    paths: list[str] = []
    for pattern in ("*.yaml", "*.yml"):
        for candidate in sorted(configs_dir.glob(pattern)):
            if not candidate.is_file():
                continue
            if candidate.name.lower().startswith("commercial"):
                continue
            payload = _load_yaml(candidate)
            if not isinstance(payload.get("asr"), dict):
                continue
            paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    discovered = _sorted_unique(paths)
    if discovered:
        return discovered
    return ["configs/default.yaml"]


def _discover_defaults(base_configs: list[str]) -> dict[str, dict[str, Any]]:
    defaults: dict[str, dict[str, Any]] = {}
    for rel_path in base_configs:
        defaults[rel_path] = _load_yaml(REPO_ROOT / rel_path)
    return defaults


def _discover_scenario_catalog(
    defaults_by_config: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    for rel_path in sorted(defaults_by_config.keys()):
        cfg = defaults_by_config.get(rel_path, {})
        web_cfg = cfg.get("web", {}) if isinstance(cfg.get("web"), dict) else {}
        label = str(web_cfg.get("scenario_label") or rel_path)
        description = str(web_cfg.get("scenario_description") or "")
        catalog.append(
            {
                "id": rel_path,
                "label": label,
                "description": description,
                "base_config": rel_path,
            }
        )
    return catalog


def _discover_repo_files(*, subdir: str, patterns: list[str]) -> list[str]:
    root = REPO_ROOT / subdir
    if not root.exists():
        return []
    files: list[str] = []
    for pattern in patterns:
        for item in sorted(root.glob(pattern)):
            if item.is_file():
                files.append(item.relative_to(REPO_ROOT).as_posix())
    return _sorted_unique(files)


def _discover_vosk_model_paths() -> list[str]:
    discovered: list[str] = []
    for rel_dir in ("models", "data/models"):
        root = REPO_ROOT / rel_dir
        if not root.exists():
            continue
        for item in sorted(root.glob("vosk-model*")):
            if item.is_dir():
                discovered.append(item.relative_to(REPO_ROOT).as_posix())
    discovered.extend(BACKEND_MODEL_PRESETS.get("vosk", []))
    return _sorted_unique(discovered)


def _discover_reference_texts() -> list[str]:
    manifest = REPO_ROOT / "data" / "transcripts" / "sample_manifest.csv"
    if not manifest.exists():
        return []

    values: list[str] = []
    with manifest.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            transcript = str(row.get("transcript") or "").strip()
            if transcript:
                values.append(transcript)
    return _sorted_unique(values)


def list_profiles() -> list[str]:
    """Return list of saved GUI profile names."""
    if not PROFILES_DIR.exists():
        return []
    names = [item.stem for item in PROFILES_DIR.glob("*.yaml")]
    return sorted(set(names))


def _discover_sso_constants_from_saved_profiles() -> tuple[list[str], list[str]]:
    start_urls: set[str] = set()
    regions: set[str] = set()
    if not PROFILES_DIR.exists():
        return [], []

    for path in PROFILES_DIR.glob("*.yaml"):
        payload = _load_yaml(path)
        start_url = str(payload.get("aws_sso_start_url", "")).strip()
        region = str(payload.get("aws_sso_region", "")).strip()
        if start_url:
            start_urls.add(start_url)
        if region:
            regions.add(region)
    return sorted(start_urls), sorted(regions)


def get_options_payload() -> dict[str, Any]:
    """Build option payload consumed by frontend."""
    base_configs = _discover_base_configs()
    defaults_by_config = _discover_defaults(base_configs)
    scenario_catalog = _discover_scenario_catalog(defaults_by_config)
    datasets = _discover_repo_files(subdir="data/transcripts", patterns=["*.csv"])
    sample_wavs = _discover_repo_files(subdir="data/sample", patterns=["*.wav"])
    reference_texts = _discover_reference_texts()
    auth_start_urls, auth_regions = discover_sso_constants()
    profile_start_urls, profile_regions = _discover_sso_constants_from_saved_profiles()
    sso_start_urls = sorted(set(auth_start_urls) | set(profile_start_urls))
    sso_regions = sorted(set(auth_regions) | set(profile_regions))

    # Backward-compatible view used by older frontend builds.
    defaults_legacy = {
        Path(path).stem: payload for path, payload in defaults_by_config.items()
    }

    return {
        "languages": LANGUAGES,
        "language_modes": LANGUAGE_MODE_OPTIONS,
        "interfaces": INTERFACE_OPTIONS,
        "backends": BACKEND_OPTIONS,
        "input_modes": INPUT_MODE_OPTIONS,
        "backend_models": BACKEND_MODEL_PRESETS,
        "whisper_devices": WHISPER_DEVICE_OPTIONS,
        "whisper_compute_types": WHISPER_COMPUTE_OPTIONS,
        "aws_regions": AWS_REGION_OPTIONS,
        "azure_regions": AZURE_REGION_OPTIONS,
        "google_regions": GOOGLE_REGION_OPTIONS,
        "vosk_model_paths": _discover_vosk_model_paths(),
        "aws_bucket_hints": AWS_BUCKET_HINTS,
        "azure_endpoint_hints": AZURE_ENDPOINT_HINTS,
        "audio_device_hints": AUDIO_DEVICE_HINTS,
        "metrics": METRIC_KEYS,
        "benchmark_scenarios": SCENARIO_OPTIONS,
        "benchmark_backend_presets": BENCHMARK_BACKEND_PRESETS,
        "benchmark_scenario_presets": BENCHMARK_SCENARIO_PRESETS,
        "model_run_presets": MODEL_RUN_PRESETS,
        "noise_level_presets": NOISE_LEVEL_PRESETS,
        "sample_rates": SAMPLE_RATE_OPTIONS,
        "chunk_ms_values": CHUNK_MS_OPTIONS,
        "benchmark_chunk_sec_values": CHUNK_SEC_OPTIONS,
        "record_sec_values": RECORD_SEC_OPTIONS,
        "action_chunk_sec_values": CHUNK_SEC_OPTIONS,
        "request_timeout_values": REQUEST_TIMEOUT_OPTIONS,
        "mic_capture_sec_values": MIC_CAPTURE_SEC_OPTIONS,
        "datasets": datasets,
        "sample_wavs": sample_wavs,
        "reference_texts": reference_texts,
        "base_configs": base_configs,
        "scenario_presets": scenario_catalog,
        "profiles": list_profiles(),
        "aws_auth_profiles": list_auth_profiles(),
        "aws_sso_start_urls": sso_start_urls,
        "aws_sso_regions": sso_regions,
        "defaults": defaults_legacy,
        "defaults_by_config": defaults_by_config,
    }
