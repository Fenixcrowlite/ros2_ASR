#!/usr/bin/env python3
"""Interactive launcher for the ROS2 ASR thesis demo."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVIDERS = {
    "1": {
        "name": "Whisper local",
        "profile": "providers/whisper_local",
        "runtime_profile": "default_runtime",
    },
    "2": {
        "name": "Vosk local",
        "profile": "providers/vosk_local",
        "runtime_profile": "default_runtime",
    },
    "3": {
        "name": "Hugging Face local",
        "profile": "providers/huggingface_local",
        "runtime_profile": "huggingface_local_runtime",
    },
    "4": {
        "name": "Hugging Face hosted API",
        "profile": "providers/huggingface_api",
        "runtime_profile": "huggingface_api_runtime",
    },
    "5": {
        "name": "Azure Speech",
        "profile": "providers/azure_cloud",
        "runtime_profile": "default_runtime",
    },
    "6": {
        "name": "Google Cloud Speech-to-Text",
        "profile": "providers/google_cloud",
        "runtime_profile": "default_runtime",
    },
    "7": {
        "name": "Amazon Transcribe",
        "profile": "providers/aws_cloud",
        "runtime_profile": "default_runtime",
    },
}


def ask_choice(title: str, options: dict[str, str]) -> str:
    print("\n" + title)
    for key, label in options.items():
        print(f"  {key}) {label}")
    while True:
        value = input("> ").strip()
        if value in options:
            return value
        print("Invalid choice. Enter one of the listed numbers.")


def ask_single_provider() -> dict[str, str]:
    key = ask_choice(
        "Select the active ASR provider:",
        {key: value["name"] for key, value in PROVIDERS.items()},
    )
    return PROVIDERS[key]


def ask_benchmark_providers() -> str:
    print("\nSelect providers for the benchmark:")
    print("  0) all providers")
    for key, value in PROVIDERS.items():
        print(f"  {key}) {value['name']}")
    print("Enter one or more comma-separated values, for example: 1,2,5")

    while True:
        raw = input("> ").replace(" ", "")
        if raw == "0":
            keys = list(PROVIDERS)
            break
        keys = raw.split(",") if raw else []
        if keys and all(key in PROVIDERS for key in keys):
            keys = list(dict.fromkeys(keys))
            break
        print("Invalid choice. Use 0 or a comma-separated list such as 1,2,5.")

    return ",".join(str(PROVIDERS[key]["profile"]) for key in keys)


def run_command(args: list[str]) -> int:
    print("\nRunning:", " ".join(args))
    return subprocess.call(args, cwd=ROOT)


def main() -> int:
    print("ROS2 ASR interactive launcher")
    mode = ask_choice(
        "Choose an action:",
        {
            "1": "start only the ROS2 runtime branch",
            "2": "run a benchmark from the console",
            "3": "start the complete system with web UI",
            "4": "stop the web UI stack",
            "5": "configure optional providers",
            "6": "exit",
        },
    )

    if mode == "6":
        return 0
    if mode == "5":
        return run_command(["make", "configure-providers"])
    if mode == "4":
        return run_command(["make", "down"])
    if mode == "3":
        return run_command(["make", "up"])
    if mode == "1":
        provider = ask_single_provider()
        return run_command(
            [
                "make",
                "up-runtime",
                f"PROVIDER_PROFILE={provider['profile']}",
                f"RUNTIME_PROFILE={provider['runtime_profile']}",
            ]
        )

    profiles = ask_benchmark_providers()
    return run_command(
        ["bash", "scripts/run_benchmark_suite_prepared.sh", "--providers", profiles]
    )


if __name__ == "__main__":
    raise SystemExit(main())
