"""Batch executor for benchmark sample x provider matrix."""

from __future__ import annotations

from typing import Any

from asr_core import make_request_id
from asr_datasets import DatasetSample
from asr_metrics.engine import MetricEngine
from asr_metrics.plugins import MetricContext
from asr_provider_base import ProviderAudio


class BatchExecutor:
    def __init__(self, metric_engine: MetricEngine) -> None:
        self.metric_engine = metric_engine

    def run_sample(
        self,
        *,
        run_id: str,
        provider,
        provider_profile: str,
        sample: DatasetSample,
        session_id: str,
    ) -> dict[str, Any]:
        audio = ProviderAudio(
            session_id=session_id,
            request_id=make_request_id(),
            language=sample.language,
            sample_rate_hz=16000,
            wav_path=sample.audio_path,
            enable_word_timestamps=True,
            metadata={"sample_id": sample.sample_id, "run_id": run_id},
        )
        result = provider.recognize_once(audio)

        context = MetricContext(
            reference_text=sample.transcript,
            hypothesis_text=result.text,
            latency_ms=result.latency.total_ms,
            success=not result.degraded and not result.error_code,
        )
        metrics = self.metric_engine.evaluate(context)

        return {
            "run_id": run_id,
            "provider_profile": provider_profile,
            "provider_id": result.provider_id,
            "sample_id": sample.sample_id,
            "success": context.success,
            "text": result.text,
            "error_code": result.error_code,
            "error_message": result.error_message,
            "metrics": metrics,
            "normalized_result": result.as_dict(),
        }
