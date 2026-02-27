from __future__ import annotations

import uuid
from pathlib import Path

from asr_core.models import AsrResponse

from asr_metrics.models import BenchmarkRecord
from asr_metrics.quality import cer, wer
from asr_metrics.system import collect_cpu_ram, collect_gpu


class MetricsCollector:
    def __init__(self, pricing_per_minute: dict[str, float] | None = None) -> None:
        self.pricing_per_minute = pricing_per_minute or {}

    def estimate_cost(self, backend: str, audio_duration_sec: float) -> float:
        ppm = self.pricing_per_minute.get(backend, 0.0)
        return (audio_duration_sec / 60.0) * ppm

    @staticmethod
    def _snr_from_scenario(scenario: str) -> float | None:
        if scenario.startswith("snr"):
            try:
                return float(scenario.replace("snr", ""))
            except ValueError:
                return None
        return None

    def record(
        self,
        *,
        backend: str,
        scenario: str,
        wav_path: str,
        language: str,
        reference_text: str,
        response: AsrResponse,
        request_id: str | None = None,
    ) -> BenchmarkRecord:
        req_id = request_id or str(uuid.uuid4())
        cpu, ram = collect_cpu_ram()
        gpu_u, gpu_m = collect_gpu()
        latency_ms = response.timings.total_ms
        duration = response.audio_duration_sec if response.audio_duration_sec > 0 else 1e-6
        rtf = latency_ms / 1000.0 / duration
        return BenchmarkRecord(
            request_id=req_id,
            audio_id=Path(wav_path).stem,
            backend=backend,
            scenario=scenario,
            snr_db=self._snr_from_scenario(scenario),
            wav_path=wav_path,
            language=language,
            duration_sec=response.audio_duration_sec,
            text=response.text,
            transcript_ref=reference_text,
            transcript_hyp=response.text,
            wer=wer(reference_text, response.text),
            cer=cer(reference_text, response.text),
            latency_ms=latency_ms,
            preprocess_ms=response.timings.preprocess_ms,
            inference_ms=response.timings.inference_ms,
            postprocess_ms=response.timings.postprocess_ms,
            audio_duration_sec=response.audio_duration_sec,
            rtf=rtf,
            cpu_percent=cpu,
            ram_mb=ram,
            gpu_util_percent=gpu_u,
            gpu_mem_mb=gpu_m,
            success=response.success,
            error_code=response.error_code,
            error_message=response.error_message,
            cost_estimate=self.estimate_cost(backend, response.audio_duration_sec),
        )
