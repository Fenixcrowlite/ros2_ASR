#!/usr/bin/env python3
"""Run one Hugging Face provider profile through the unified ASR adapter."""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any


def _bootstrap_imports() -> Path:
    current = Path(__file__).resolve()
    project_root = current.parent.parent
    src_root = project_root / "ros2_ws" / "src"

    paths = [project_root]
    if src_root.is_dir():
        paths.extend(path for path in src_root.iterdir() if path.is_dir())

    for candidate in reversed(paths):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)
    return project_root


PROJECT_ROOT = _bootstrap_imports()

from asr_config import resolve_profile  # noqa: E402
from asr_core import make_request_id, make_session_id  # noqa: E402
from asr_metrics import text_quality_support  # noqa: E402
from asr_provider_base import ProviderAudio, ProviderManager  # noqa: E402
from asr_provider_base.config import resolve_provider_selection_from_runtime_payload  # noqa: E402


def _normalize_profile_ref(value: str, *, prefix: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if normalized.startswith(f"{prefix}/"):
        return normalized
    return f"{prefix}/{normalized}"


def _parse_json_object(raw: str, *, label: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return payload


def _wav_metadata(wav_path: Path) -> dict[str, int]:
    with wave.open(str(wav_path), "rb") as handle:
        return {
            "sample_rate_hz": int(handle.getframerate()),
            "channels": int(handle.getnchannels()),
            "sample_width_bytes": int(handle.getsampwidth()),
        }


def _resolve_runtime_defaults(
    *,
    runtime_profile: str,
    configs_root: Path,
) -> dict[str, Any]:
    normalized = _normalize_profile_ref(runtime_profile, prefix="runtime")
    if not normalized:
        return {}
    runtime_cfg = resolve_profile(
        profile_type="runtime",
        profile_id=normalized.split("/", 1)[1],
        configs_root=str(configs_root),
    )
    provider_selection = resolve_provider_selection_from_runtime_payload(runtime_cfg.data)
    orchestrator_cfg = (
        runtime_cfg.data.get("orchestrator", {})
        if isinstance(runtime_cfg.data.get("orchestrator", {}), dict)
        else {}
    )
    audio_cfg = runtime_cfg.data.get("audio", {}) if isinstance(runtime_cfg.data.get("audio", {}), dict) else {}
    return {
        "provider_profile": provider_selection.profile,
        "provider_preset": provider_selection.preset,
        "provider_settings": dict(provider_selection.settings),
        "language": str(orchestrator_cfg.get("language", "") or ""),
        "wav_path": str(audio_cfg.get("file_path", "") or ""),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Hugging Face provider smoke test")
    parser.add_argument("--configs-root", default=str(PROJECT_ROOT / "configs"))
    parser.add_argument("--runtime-profile", default="")
    parser.add_argument("--provider-profile", default="providers/huggingface_local")
    parser.add_argument("--preset", default="")
    parser.add_argument("--settings-json", default="{}")
    parser.add_argument("--wav", default="")
    parser.add_argument("--language", default="")
    parser.add_argument("--reference-text", default="")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--request-id", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--disable-word-timestamps", action="store_true")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    configs_root = Path(args.configs_root).resolve()
    runtime_defaults = _resolve_runtime_defaults(
        runtime_profile=str(args.runtime_profile or "").strip(),
        configs_root=configs_root,
    )
    provider_profile = _normalize_profile_ref(
        str(args.provider_profile or runtime_defaults.get("provider_profile", "")).strip(),
        prefix="providers",
    )
    if not provider_profile:
        raise SystemExit("A provider profile is required")

    provider_preset = str(args.preset or runtime_defaults.get("provider_preset", "") or "").strip()
    provider_settings = dict(runtime_defaults.get("provider_settings", {}) or {})
    provider_settings.update(_parse_json_object(args.settings_json, label="settings-json"))

    wav_value = str(args.wav or runtime_defaults.get("wav_path", "") or "").strip()
    wav_path = Path(wav_value if wav_value else PROJECT_ROOT / "data" / "sample" / "vosk_test.wav")
    if not wav_path.is_absolute():
        wav_path = (PROJECT_ROOT / wav_path).resolve()
    if not wav_path.exists():
        raise SystemExit(f"WAV file not found: {wav_path}")

    language = str(args.language or runtime_defaults.get("language", "") or "en-US").strip()
    audio_meta = _wav_metadata(wav_path)

    manager = ProviderManager(configs_root=str(configs_root))
    provider = manager.create_from_profile(
        provider_profile,
        preset_id=provider_preset,
        settings_overrides=provider_settings,
    )
    try:
        result = provider.recognize_once(
            ProviderAudio(
                session_id=str(args.session_id or "").strip() or make_session_id(),
                request_id=str(args.request_id or "").strip() or make_request_id(),
                language=language,
                sample_rate_hz=audio_meta["sample_rate_hz"],
                wav_path=str(wav_path),
                enable_word_timestamps=not bool(args.disable_word_timestamps),
                metadata={
                    "channels": audio_meta["channels"],
                    "sample_width_bytes": audio_meta["sample_width_bytes"],
                },
            )
        )
        quality_metrics: dict[str, Any] = {}
        reference_text = str(args.reference_text or "").strip()
        if reference_text:
            quality = text_quality_support(reference_text, result.text)
            quality_metrics = {
                "wer": float(quality.wer),
                "cer": float(quality.cer),
                "sample_accuracy": 1.0 if result.text.strip() == reference_text.strip() else 0.0,
            }

        payload = {
            "provider_profile": provider_profile,
            "provider_preset": provider_preset,
            "provider_id": result.provider_id,
            "wav_path": str(wav_path),
            "language": language,
            "success": not bool(result.error_code),
            "degraded": bool(result.degraded),
            "text": result.text,
            "confidence": float(result.confidence),
            "confidence_available": bool(result.confidence_available),
            "timestamps_available": bool(result.timestamps_available),
            "word_count": len(result.words),
            "words": [
                {
                    "word": word.word,
                    "start_sec": float(word.start_sec),
                    "end_sec": float(word.end_sec),
                    "confidence": float(word.confidence),
                    "confidence_available": bool(word.confidence_available),
                }
                for word in result.words
            ],
            "latency": {
                "total_ms": float(result.latency.total_ms),
                "preprocess_ms": float(result.latency.preprocess_ms),
                "inference_ms": float(result.latency.inference_ms),
                "postprocess_ms": float(result.latency.postprocess_ms),
            },
            "quality_metrics": quality_metrics,
            "provider_metadata": provider.get_metadata().__dict__,
            "provider_runtime_metrics": provider.get_metrics().as_dict(),
            "provider_status": provider.get_status().__dict__,
        }
    finally:
        provider.teardown()

    rendered = json.dumps(payload, ensure_ascii=True, indent=2)
    if str(args.output or "").strip():
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
