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


@dataclass(slots=True)
class ProviderMetadata:
    provider_id: str
    display_name: str = ""
    implementation: str = ""
    model_id: str = ""
    endpoint: str = ""
    device: str = ""
    revision: str = ""
    source: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderRuntimeMetrics:
    model_load_ms: float = 0.0
    requests_total: int = 0
    stream_sessions_total: int = 0
    last_latency_ms: float = 0.0
    average_latency_ms: float = 0.0
    errors_total: int = 0
    last_error_code: str = ""
    last_error_message: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_load_ms": float(self.model_load_ms),
            "requests_total": int(self.requests_total),
            "stream_sessions_total": int(self.stream_sessions_total),
            "last_latency_ms": float(self.last_latency_ms),
            "average_latency_ms": float(self.average_latency_ms),
            "errors_total": int(self.errors_total),
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
            "extra": dict(self.extra),
        }
