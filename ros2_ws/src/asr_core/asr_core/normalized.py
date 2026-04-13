"""Normalized provider-agnostic ASR result model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizedWord:
    """Provider-neutral word-level timing entry."""

    word: str
    start_sec: float
    end_sec: float
    confidence: float = 0.0
    confidence_available: bool = False


@dataclass(slots=True)
class LatencyMetadata:
    """Canonical latency breakdown attached to normalized ASR results."""

    total_ms: float = 0.0
    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    postprocess_ms: float = 0.0
    first_partial_ms: float = 0.0
    finalization_ms: float = 0.0


@dataclass(slots=True)
class NormalizedAsrResult:
    """Canonical result model shared across runtime, benchmark, and gateway code."""

    request_id: str
    session_id: str
    provider_id: str
    text: str
    is_final: bool
    is_partial: bool
    utterance_start_sec: float = 0.0
    utterance_end_sec: float = 0.0
    audio_duration_sec: float = 0.0
    words: list[NormalizedWord] = field(default_factory=list)
    confidence: float = 0.0
    confidence_available: bool = False
    timestamps_available: bool = False
    language: str = ""
    language_detected: bool = False
    latency: LatencyMetadata = field(default_factory=LatencyMetadata)
    raw_metadata_ref: str = ""
    degraded: bool = False
    error_code: str = ""
    error_message: str = ""
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize nested dataclasses into a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["words"] = [asdict(word) for word in self.words]
        payload["latency"] = asdict(self.latency)
        return payload


@dataclass(slots=True)
class SessionState:
    """Minimal runtime session status projection."""

    session_id: str
    state: str
    provider_id: str
    profile_id: str
    status_message: str = ""
    error_code: str = ""
    error_message: str = ""
