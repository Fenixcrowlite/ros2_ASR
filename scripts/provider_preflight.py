#!/usr/bin/env python3
"""Validate a selected ASR provider before launching runtime processes."""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

REQUIRED_MODULES: dict[str, tuple[str, ...]] = {
    "providers/whisper_local": ("faster_whisper",),
    "providers/vosk_local": ("vosk",),
    "providers/huggingface_local": ("torch", "transformers"),
    "providers/huggingface_api": ("requests",),
    "providers/azure_cloud": ("azure.cognitiveservices.speech",),
    "providers/google_cloud": ("google.cloud.speech",),
    "providers/aws_cloud": ("boto3", "amazon_transcribe"),
}


def add_workspace_sources(root: Path) -> None:
    src_root = root / "ros2_ws" / "src"
    sys.path.insert(0, str(root))
    for package_dir in sorted(src_root.iterdir()):
        if package_dir.is_dir():
            sys.path.insert(0, str(package_dir))


def require_provider_modules(profile: str) -> None:
    failures: list[str] = []
    for module_name in REQUIRED_MODULES.get(profile, ()):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {exc}")
    if failures:
        raise RuntimeError("Required Python modules are unavailable: " + "; ".join(failures))


def materialize_local_provider(profile: str, provider: Any) -> None:
    if profile == "providers/whisper_local":
        backend = getattr(provider, "_backend", None)
        loader = getattr(backend, "_load_model", None)
        if callable(loader) and not loader():
            detail = str(getattr(backend, "_load_error", "") or "unknown error")
            raise RuntimeError(f"Whisper model preparation failed: {detail}")
    elif profile == "providers/vosk_local":
        backend = getattr(provider, "_backend", None)
        loader = getattr(backend, "_load_vosk", None)
        if callable(loader) and not loader():
            detail = str(getattr(backend, "_last_load_error", "") or "unknown error")
            raise RuntimeError(f"Vosk model preparation failed: {detail}")
    elif profile == "providers/huggingface_local":
        loader = getattr(provider, "_load_pipeline", None)
        if callable(loader):
            loader()


def validate_operational_requirements(
    profile: str,
    provider: Any,
    *,
    require_batch_assets: bool,
) -> None:
    if profile == "providers/aws_cloud" and require_batch_assets:
        backend = getattr(provider, "_backend", None)
        bucket = str(getattr(backend, "s3_bucket", "") or "").strip()
        if not bucket:
            raise RuntimeError(
                "AWS S3 bucket is missing. Provide AWS_S3_BUCKET for bundled WAV tests and batch jobs."
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--configs-root", default="configs")
    parser.add_argument(
        "--require-batch-assets",
        action="store_true",
        help="Require assets needed for batch or bundled-WAV execution, such as an AWS S3 bucket.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    add_workspace_sources(root)
    provider: Any | None = None
    try:
        require_provider_modules(args.profile)
        from asr_provider_base.manager import ProviderManager

        manager = ProviderManager(configs_root=str(root / args.configs_root))
        provider = manager.create_from_profile(args.profile)
        validate_operational_requirements(
            args.profile,
            provider,
            require_batch_assets=bool(args.require_batch_assets),
        )
        materialize_local_provider(args.profile, provider)
    except Exception as exc:
        print(f"ERROR: selected provider is not ready: {args.profile}", file=sys.stderr)
        print(f"DETAIL: {exc}", file=sys.stderr)
        print("Fix the reported setup issue or choose another provider.", file=sys.stderr)
        return 1
    finally:
        if provider is not None:
            try:
                provider.teardown()
            except Exception:
                pass

    print(f"PASS: selected provider is ready: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
