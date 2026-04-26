"""Configuration validation helpers."""

from __future__ import annotations

import math
from typing import Any

from asr_metrics.definitions import validate_metric_names

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
    """Validate the resolved runtime profile payload used by runtime nodes."""
    errors: list[str] = []
    for key in REQUIRED_RUNTIME_KEYS:
        if key not in payload:
            errors.append(f"Missing runtime key: {key}")

    audio = payload.get("audio", {})
    if isinstance(audio, dict):
        source = str(audio.get("source", "file") or "file").strip()
        if source not in {"file", "mic"}:
            errors.append(f"audio.source must be one of: file, mic (got {source!r})")
        sample_rate = int(audio.get("sample_rate_hz", 0) or 0)
        if sample_rate <= 0:
            errors.append("audio.sample_rate_hz must be > 0")
        chunk_ms = int(audio.get("chunk_ms", 0) or 0)
        if chunk_ms <= 0:
            errors.append("audio.chunk_ms must be > 0")
        file_replay_rate = float(audio.get("file_replay_rate", 1.0) or 0.0)
        if file_replay_rate < 0.0:
            errors.append("audio.file_replay_rate must be >= 0")
        mic_capture_sec = float(audio.get("mic_capture_sec", 0.0) or 0.0)
        if mic_capture_sec < 0.0:
            errors.append("audio.mic_capture_sec must be >= 0")
        if source == "file" and not str(audio.get("file_path", "") or "").strip():
            errors.append("audio.file_path must be set when audio.source=file")
    else:
        errors.append("audio must be an object")

    preprocess = payload.get("preprocess", {})
    if isinstance(preprocess, dict):
        target_sample_rate = int(preprocess.get("target_sample_rate_hz", 0) or 0)
        if target_sample_rate <= 0:
            errors.append("preprocess.target_sample_rate_hz must be > 0")
    else:
        errors.append("preprocess must be an object")

    vad = payload.get("vad", {})
    if isinstance(vad, dict):
        for key in (
            "energy_threshold",
            "pre_roll_ms",
            "max_silence_ms",
            "min_segment_ms",
            "max_segment_ms",
        ):
            value = int(vad.get(key, 0) or 0)
            if value < 0:
                errors.append(f"vad.{key} must be >= 0")
        min_segment_ms = int(vad.get("min_segment_ms", 0) or 0)
        max_segment_ms = int(vad.get("max_segment_ms", 0) or 0)
        if max_segment_ms > 0 and min_segment_ms > max_segment_ms:
            errors.append("vad.min_segment_ms must be <= vad.max_segment_ms")
    else:
        errors.append("vad must be an object")

    orchestrator = payload.get("orchestrator", {})
    providers = payload.get("providers", {})
    if isinstance(orchestrator, dict):
        processing_mode = str(
            orchestrator.get("processing_mode", "segmented") or "segmented"
        ).strip()
        if processing_mode not in {"segmented", "provider_stream"}:
            errors.append("orchestrator.processing_mode must be one of: segmented, provider_stream")
    else:
        errors.append("orchestrator must be an object")
        orchestrator = {}

    if providers and not isinstance(providers, dict):
        errors.append("providers must be an object")
        providers = {}

    selected_provider = str(
        (providers.get("active", "") if isinstance(providers, dict) else "")
        or orchestrator.get("provider_profile", "")
        or ""
    ).strip()
    if not selected_provider:
        errors.append(
            "runtime provider must be set via orchestrator.provider_profile or providers.active"
        )
    if isinstance(providers, dict):
        provider_settings = providers.get("settings", {})
        if provider_settings and not isinstance(provider_settings, dict):
            errors.append("providers.settings must be an object")

    session = payload.get("session", {})
    if isinstance(session, dict):
        max_concurrent_sessions = int(session.get("max_concurrent_sessions", 0) or 0)
        if max_concurrent_sessions <= 0:
            errors.append("session.max_concurrent_sessions must be > 0")
    else:
        errors.append("session must be an object")

    return errors


def validate_benchmark_payload(payload: dict[str, Any]) -> list[str]:
    """Validate the resolved benchmark profile payload before execution."""
    errors: list[str] = []
    supported_noise_levels = {"clean", "light", "medium", "heavy", "extreme"}
    supported_noise_modes = {"white", "pink", "brown", "babble", "hum"}
    for key in REQUIRED_BENCHMARK_KEYS:
        if key not in payload:
            errors.append(f"Missing benchmark key: {key}")

    dataset_profile = str(payload.get("dataset_profile", "") or "").strip()
    if not dataset_profile:
        errors.append("dataset_profile must be a non-empty string")

    providers = payload.get("providers", [])
    if not isinstance(providers, list) or not providers:
        errors.append("providers must be a non-empty list")
    elif not all(str(item or "").strip() for item in providers):
        errors.append("providers entries must be non-empty strings")

    metric_profiles = payload.get("metric_profiles", [])
    if not isinstance(metric_profiles, list) or not metric_profiles:
        errors.append("metric_profiles must be a non-empty list")
    elif not all(str(item or "").strip() for item in metric_profiles):
        errors.append("metric_profiles entries must be non-empty strings")

    execution_mode = str(payload.get("execution_mode", "batch") or "batch").strip()
    if execution_mode not in {"batch", "streaming"}:
        errors.append("execution_mode must be one of: batch, streaming")

    batch_cfg = payload.get("batch", {})
    if batch_cfg and not isinstance(batch_cfg, dict):
        errors.append("batch must be an object")
    elif isinstance(batch_cfg, dict):
        if "max_samples" in batch_cfg:
            max_samples = int(batch_cfg.get("max_samples", 0) or 0)
            if max_samples < 0:
                errors.append("batch.max_samples must be >= 0")
        if "timeout_sec" in batch_cfg:
            timeout_sec = float(batch_cfg.get("timeout_sec", 0.0) or 0.0)
            if timeout_sec <= 0.0:
                errors.append("batch.timeout_sec must be > 0")

    streaming_cfg = payload.get("streaming", {})
    if streaming_cfg and not isinstance(streaming_cfg, dict):
        errors.append("streaming must be an object")
    elif isinstance(streaming_cfg, dict):
        if "chunk_ms" in streaming_cfg:
            chunk_ms = int(streaming_cfg.get("chunk_ms", 0) or 0)
            if chunk_ms <= 0:
                errors.append("streaming.chunk_ms must be > 0")
        if "replay_rate" in streaming_cfg:
            replay_rate = float(streaming_cfg.get("replay_rate", 0.0) or 0.0)
            if replay_rate < 0.0:
                errors.append("streaming.replay_rate must be >= 0")

    noise_cfg = payload.get("noise", {})
    if noise_cfg and not isinstance(noise_cfg, dict):
        errors.append("noise must be an object")
    elif isinstance(noise_cfg, dict):
        if "mode" in noise_cfg:
            mode = str(noise_cfg.get("mode", "") or "").strip().lower()
            if mode and mode not in supported_noise_modes:
                errors.append(
                    "noise.mode must be one of: "
                    + ", ".join(sorted(supported_noise_modes))
                )
        if "levels" in noise_cfg:
            levels = noise_cfg.get("levels", [])
            if isinstance(levels, str):
                levels = [item.strip() for item in levels.split(",") if item.strip()]
            if not isinstance(levels, list):
                errors.append("noise.levels must be a list or comma-separated string")
            else:
                normalized_levels = [str(item or "").strip().lower() for item in levels]
                if any(not item for item in normalized_levels):
                    errors.append("noise.levels entries must be non-empty strings")
                invalid_levels = sorted(
                    {item for item in normalized_levels if item and item not in supported_noise_levels}
                )
                if invalid_levels:
                    errors.append(
                        "noise.levels contains unsupported values: "
                        + ", ".join(invalid_levels)
                    )
        if "seed" in noise_cfg:
            try:
                int(noise_cfg.get("seed", 0) or 0)
            except (TypeError, ValueError):
                errors.append("noise.seed must be an integer")
        if "custom_snr_db" in noise_cfg:
            custom_snr_db = noise_cfg.get("custom_snr_db", [])
            if isinstance(custom_snr_db, str):
                custom_snr_db = [item.strip() for item in custom_snr_db.split(",") if item.strip()]
            if not isinstance(custom_snr_db, list):
                errors.append("noise.custom_snr_db must be a list or comma-separated string")
            else:
                for item in custom_snr_db:
                    try:
                        value = float(item)
                    except (TypeError, ValueError):
                        errors.append("noise.custom_snr_db entries must be numeric")
                        continue
                    if not math.isfinite(value):
                        errors.append("noise.custom_snr_db entries must be finite")
                        continue
                    if value < -5.0 or value > 60.0:
                        errors.append("noise.custom_snr_db entries must be between -5 and 60 dB")

    return errors


def validate_metric_payload(payload: dict[str, Any]) -> list[str]:
    """Validate a metric selection payload against the metric registry."""
    errors: list[str] = []
    metrics = payload.get("metrics", [])
    if not isinstance(metrics, list) or not metrics:
        return ["metrics must be a non-empty list"]

    normalized = [str(item or "").strip() for item in metrics]
    if any(not item for item in normalized):
        errors.append("metrics entries must be non-empty strings")
        normalized = [item for item in normalized if item]

    errors.extend(validate_metric_names(normalized))
    return errors
