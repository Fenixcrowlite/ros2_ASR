from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class BenchmarkRecord:
    request_id: str
    audio_id: str
    backend: str
    scenario: str
    snr_db: float | None
    wav_path: str
    language: str
    duration_sec: float
    text: str
    transcript_ref: str
    transcript_hyp: str
    wer: float
    cer: float
    latency_ms: float
    preprocess_ms: float
    inference_ms: float
    postprocess_ms: float
    audio_duration_sec: float
    rtf: float
    cpu_percent: float
    ram_mb: float
    gpu_util_percent: float
    gpu_mem_mb: float
    success: bool
    error_code: str
    error_message: str
    cost_estimate: float

    def to_dict(self) -> dict:
        return asdict(self)
