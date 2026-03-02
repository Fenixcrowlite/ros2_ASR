"""Language code normalization helpers shared by all ASR layers."""

from __future__ import annotations

from typing import Final

LANGUAGE_CODE_MAP: Final[dict[str, str]] = {
    "ar": "ar-SA",
    "cs": "cs-CZ",
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "hi": "hi-IN",
    "it": "it-IT",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "pt": "pt-PT",
    "ru": "ru-RU",
    "sk": "sk-SK",
    "tr": "tr-TR",
    "uk": "uk-UA",
    "zh": "zh-CN",
}


def normalize_language_code(raw: str, fallback: str = "en-US") -> str:
    """Normalize language code into canonical BCP-47-like form.

    Examples:
    - ``sk`` -> ``sk-SK``
    - ``sk_sk`` -> ``sk-SK``
    - ``SK-sk`` -> ``sk-SK``
    """
    value = str(raw or "").strip().replace("_", "-")
    if not value:
        return fallback

    lowered = value.lower()
    mapped = LANGUAGE_CODE_MAP.get(lowered)
    if mapped:
        return mapped

    if "-" in value:
        prefix, suffix = value.split("-", 1)
        normalized = f"{prefix.lower()}-{suffix.upper()}"
        mapped_prefix = LANGUAGE_CODE_MAP.get(prefix.lower())
        if mapped_prefix and mapped_prefix.split("-", 1)[1] == suffix.upper():
            return mapped_prefix
        return normalized

    return LANGUAGE_CODE_MAP.get(lowered, fallback if fallback else value)
