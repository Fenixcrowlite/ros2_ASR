"""Provider adapter request/response models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderAudio:
    session_id: str
    request_id: str
    language: str
    sample_rate_hz: int
    audio_bytes: bytes = b""
    wav_path: str = ""
    enable_word_timestamps: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderStatus:
    provider_id: str
    state: str
    message: str = ""
    health: str = "ok"
    error_code: str = ""
    error_message: str = ""
