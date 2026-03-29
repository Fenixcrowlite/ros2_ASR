"""Provider-agnostic data models exchanged across core/ROS/bench layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WordTimestamp:
    """Per-word alignment item returned by backend when available."""

    word: str
    start_sec: float
    end_sec: float
    confidence: float = 0.0


@dataclass(slots=True)
class AsrTimings:
    """Latency breakdown in milliseconds."""

    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    postprocess_ms: float = 0.0

    @property
    def total_ms(self) -> float:
        """Total latency used by metrics and ROS messages."""
        return self.preprocess_ms + self.inference_ms + self.postprocess_ms


@dataclass(slots=True)
class AsrRequest:
    """Unified input request for all backends.

    Fields:
    - `wav_path`: path to WAV file.
    - `audio_bytes`: in-memory audio payload when no file path is used.
    - `language`: requested language code.
    - `enable_word_timestamps`: whether word-level timings are needed.
    - `sample_rate`: sample rate hint for in-memory payload handling.
    - `metadata`: optional flags for backend internals.
    """

    wav_path: str | None = None
    audio_bytes: bytes | None = None
    language: str = "en-US"
    enable_word_timestamps: bool = True
    sample_rate: int = 16000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackendCapabilities:
    """Feature matrix exposed by each backend."""

    supports_recognize_once: bool = True
    supports_streaming: bool = False
    streaming_mode: str = "none"  # none | native
    supports_word_timestamps: bool = False
    supports_confidence: bool = False
    is_cloud: bool = False


@dataclass(slots=True)
class AsrResponse:
    """Normalized output from every backend."""

    text: str = ""
    partials: list[str] = field(default_factory=list)
    confidence: float = 0.0
    word_timestamps: list[WordTimestamp] = field(default_factory=list)
    language: str = ""
    backend_info: dict[str, str] = field(default_factory=dict)
    timings: AsrTimings = field(default_factory=AsrTimings)
    audio_duration_sec: float = 0.0
    success: bool = True
    error_code: str = ""
    error_message: str = ""
    raw_response: Any = None

    def as_dict(self) -> dict[str, Any]:
        """Serialize response for JSON reporting."""
        return {
            "text": self.text,
            "partials": self.partials,
            "confidence": self.confidence,
            "word_timestamps": [
                {
                    "word": w.word,
                    "start_sec": w.start_sec,
                    "end_sec": w.end_sec,
                    "confidence": w.confidence,
                }
                for w in self.word_timestamps
            ],
            "language": self.language,
            "backend_info": self.backend_info,
            "timings": {
                "preprocess_ms": self.timings.preprocess_ms,
                "inference_ms": self.timings.inference_ms,
                "postprocess_ms": self.timings.postprocess_ms,
                "total_ms": self.timings.total_ms,
            },
            "audio_duration_sec": self.audio_duration_sec,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
