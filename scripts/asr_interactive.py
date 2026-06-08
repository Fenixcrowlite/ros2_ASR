#!/usr/bin/env python3
"""Interactive launcher for the ROS2 ASR thesis demo."""
from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVIDERS = {
    "1": {
        "name": "Whisper local",
        "profile": "providers/whisper_local",
        "env": [],
    },
    "2": {
        "name": "Vosk local",
        "profile": "providers/vosk_local",
        "env": [],
    },
    "3": {
        "name": "AWS Transcribe",
        "profile": "providers/aws_cloud",
        "env": [
            ("AWS_ACCESS_KEY_ID", "AWS access key ID", False),
            ("AWS_SECRET_ACCESS_KEY", "AWS secret access key", True),
            ("AWS_DEFAULT_REGION", "AWS region", False),
            ("ASR_AWS_S3_BUCKET", "S3 bucket", False),
        ],
    },
    "4": {
        "name": "Azure Speech",
        "profile": "providers/azure_cloud",
        "env": [
            ("AZURE_SPEECH_KEY", "Azure Speech key", True),
            ("AZURE_SPEECH_REGION", "Azure Speech region", False),
        ],
    },
    "5": {
        "name": "Google Cloud Speech-to-Text",
        "profile": "providers/google_cloud",
        "env": [
            ("GOOGLE_APPLICATION_CREDENTIALS", "Path to service account JSON", False),
            ("GOOGLE_CLOUD_PROJECT", "Google Cloud project ID", False),
        ],
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
        print("Neplatná voľba. Zadaj číslo zo zoznamu.")


def ask_value(key: str, label: str, secret: bool) -> str | None:
    current = os.environ.get(key, "")
    state = "set" if current else "empty"
    prompt = f"{label} [{key}, current: {state}, Enter = ponechať]: "
    value = getpass.getpass(prompt) if secret else input(prompt)
    value = value.strip()
    return value or current or None


def collect_provider_env(provider_keys: list[str]) -> dict[str, str]:
    env_updates: dict[str, str] = {}
    for provider_key in provider_keys:
        provider = PROVIDERS[provider_key]
        print(f"\nProvider: {provider['name']}")
        for key, label, secret in provider["env"]:
            value = ask_value(str(key), str(label), bool(secret))
            if value:
                env_updates[str(key)] = value
    return env_updates


def ask_single_provider() -> tuple[str, dict[str, str]]:
    key = ask_choice(
        "Vyber aktívneho ASR providera:",
        {key: value["name"] for key, value in PROVIDERS.items()},
    )
    return str(PROVIDERS[key]["profile"]), collect_provider_env([key])


def ask_benchmark_providers() -> tuple[str, dict[str, str]]:
    print("\nVyber providerov pre benchmark:")
    print("  0) všetci provideri")
    for key, value in PROVIDERS.items():
        print(f"  {key}) {value['name']}")
    print("Zadaj jednu alebo viac možností oddelených čiarkou, napr. 1,2,4")

    while True:
        raw = input("> ").replace(" ", "")
        if raw == "0":
            keys = list(PROVIDERS)
            break
        keys = raw.split(",") if raw else []
        if keys and all(key in PROVIDERS for key in keys):
            keys = list(dict.fromkeys(keys))
            break
        print("Neplatná voľba. Použi 0 alebo zoznam, napr. 1,2,4.")

    profiles = ",".join(str(PROVIDERS[key]["profile"]) for key in keys)
    return profiles, collect_provider_env(keys)


def run_command(args: list[str], extra_env: dict[str, str] | None = None) -> int:
    env = os.environ.copy()
    env.update(extra_env or {})
    print("\nSpúšťam:", " ".join(args))
    return subprocess.call(args, cwd=ROOT, env=env)


def main() -> int:
    print("ROS2 ASR interactive launcher")
    mode = ask_choice(
        "Čo chceš spustiť?",
        {
            "1": "iba runtime vetvu ROS2",
            "2": "benchmark z konzoly",
            "3": "web GUI - spustiť celý systém",
            "4": "zastaviť web GUI",
            "5": "koniec",
        },
    )

    if mode == "5":
        return 0
    if mode == "4":
        return run_command(["make", "down"])
    if mode == "3":
        return run_command(["make", "up"])
    if mode == "1":
        profile, env = ask_single_provider()
        return run_command(["make", "up-runtime", f"PROVIDER_PROFILE={profile}"], env)

    profiles, env = ask_benchmark_providers()
    return run_command(
        ["bash", "scripts/run_benchmark_suite.sh", "--providers", profiles],
        env,
    )


if __name__ == "__main__":
    raise SystemExit(main())
