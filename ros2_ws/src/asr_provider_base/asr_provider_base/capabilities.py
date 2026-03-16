"""Provider capability model used by orchestrator and benchmark layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderCapabilities:
    supports_streaming: bool = False
    streaming_mode: str = "none"  # none | simulated | native
    supports_batch: bool = True
    supports_word_timestamps: bool = False
    supports_partials: bool = False
    supports_confidence: bool = False
    supports_language_auto_detect: bool = False
    supports_cpu: bool = True
    supports_gpu: bool = False
    requires_network: bool = False
    cost_model_type: str = "none"
    max_session_seconds: int = 0
    max_audio_seconds: int = 0
