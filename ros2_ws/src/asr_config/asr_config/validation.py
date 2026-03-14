"""Configuration validation helpers."""

from __future__ import annotations

from typing import Any


REQUIRED_RUNTIME_KEYS = (
    "audio",
    "preprocess",
    "vad",
    "orchestrator",
)


REQUIRED_BENCHMARK_KEYS = (
    "dataset_profile",
    "providers",
    "metric_profiles",
)


def validate_runtime_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_RUNTIME_KEYS:
        if key not in payload:
            errors.append(f"Missing runtime key: {key}")
    audio = payload.get("audio", {})
    if isinstance(audio, dict):
        sample_rate = int(audio.get("sample_rate_hz", 0) or 0)
        if sample_rate <= 0:
            errors.append("audio.sample_rate_hz must be > 0")
    else:
        errors.append("audio must be an object")
    return errors


def validate_benchmark_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_BENCHMARK_KEYS:
        if key not in payload:
            errors.append(f"Missing benchmark key: {key}")
    providers = payload.get("providers", [])
    if not isinstance(providers, list) or not providers:
        errors.append("providers must be a non-empty list")
    return errors
