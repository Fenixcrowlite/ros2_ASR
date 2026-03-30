"""Batch executor for benchmark sample x provider matrix."""

from __future__ import annotations

from time import perf_counter, sleep
from typing import Any

from asr_core import make_request_id
from asr_core.audio import wav_duration_sec, wav_info, wav_pcm_chunks
from asr_datasets import DatasetSample
from asr_metrics.engine import MetricEngine
from asr_metrics.plugins import MetricContext
from asr_metrics.quality import require_quality_reference, text_quality_support
from asr_provider_base import ProviderAudio
from metrics import FileTraceExporter, ObservabilityConfig, PipelineTraceCollector, build_benchmark_trace


class BatchExecutor:
    def __init__(
        self,
        metric_engine: MetricEngine,
        *,
        observability_config: ObservabilityConfig | None = None,
        trace_exporter: FileTraceExporter | None = None,
        run_dir: str = "",
    ) -> None:
        self.metric_engine = metric_engine
        self.observability_config = observability_config
        self.trace_exporter = trace_exporter
        self.run_dir = run_dir

    @staticmethod
    def _stream_replay_rate(execution_meta: dict[str, Any]) -> float:
        return max(float(execution_meta.get("streaming_replay_rate", 1.0) or 0.0), 0.0)

    def _require_quality_reference(self, sample: DatasetSample) -> None:
        if not any(
            metric_name in {"wer", "cer", "sample_accuracy"}
            for metric_name in self.metric_engine.enabled_metrics
        ):
            return
        require_quality_reference(
            sample.transcript,
            context=f"Benchmark sample `{sample.sample_id}` quality metrics",
        )

    def run_sample(
        self,
        *,
        run_id: str,
        provider,
        provider_profile: str,
        sample: DatasetSample,
        session_id: str,
        sample_audio_path: str | None = None,
        execution_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        execution_meta = execution_meta or {}
        active_audio_path = str(sample_audio_path or sample.audio_path)
        audio_duration_sec = float(sample.duration_sec or 0.0)
        if audio_duration_sec <= 0.0:
            try:
                audio_duration_sec = float(wav_duration_sec(active_audio_path))
            except Exception:
                audio_duration_sec = 0.0

        audio = ProviderAudio(
            session_id=session_id,
            request_id=make_request_id(),
            language=sample.language,
            sample_rate_hz=16000,
            wav_path=active_audio_path,
            enable_word_timestamps=True,
            metadata={
                "sample_id": sample.sample_id,
                "run_id": run_id,
                "execution": execution_meta,
            },
        )
        trace_collector = PipelineTraceCollector(
            trace_type="benchmark_sample",
            request_id=audio.request_id,
            session_id=session_id,
            run_id=run_id,
            provider_id=getattr(provider, "provider_id", ""),
            metadata={
                "provider_profile": provider_profile,
                "sample_id": sample.sample_id,
                "scenario": execution_meta.get("scenario", "clean_baseline"),
                "noise_level": execution_meta.get("noise_level", "clean"),
                "input_audio_path": active_audio_path,
            },
        )
        with trace_collector.stage(
            "provider_recognize",
            component=getattr(provider, "provider_id", "provider"),
            code_path=f"{type(provider).__module__}.{type(provider).__name__}.recognize_once",
            input_summary={
                "audio_duration_sec": audio_duration_sec,
                "language": sample.language,
                "provider_profile": provider_profile,
            },
        ) as stage_output:
            result = provider.recognize_once(audio)
            stage_output["latency_ms"] = float(result.latency.total_ms)
            stage_output["success"] = not bool(result.error_code)
            stage_output["provider_id"] = result.provider_id
            stage_output["text_length"] = len(str(result.text or ""))

        estimated_cost_usd = float(execution_meta.get("estimated_cost_usd", 0.0) or 0.0)
        self._require_quality_reference(sample)
        quality_support = text_quality_support(sample.transcript, result.text)
        context = MetricContext(
            reference_text=sample.transcript,
            hypothesis_text=result.text,
            latency_ms=result.latency.total_ms,
            success=not result.degraded and not result.error_code,
            execution_mode=str(execution_meta.get("execution_mode", "batch") or "batch"),
            audio_duration_sec=audio_duration_sec,
            estimated_cost_usd=estimated_cost_usd,
            quality_support=quality_support,
        )
        metrics = self.metric_engine.evaluate(context)
        metrics["confidence"] = float(result.confidence)
        metrics["preprocess_ms"] = float(result.latency.preprocess_ms)
        metrics["inference_ms"] = float(result.latency.inference_ms)
        metrics["postprocess_ms"] = float(result.latency.postprocess_ms)
        trace_artifact_ref = ""
        trace_corrupted = False
        if self.observability_config is not None and self.trace_exporter is not None and self.run_dir:
            trace = build_benchmark_trace(
                collector=trace_collector,
                config=self.observability_config,
                provider_id=result.provider_id,
                text=result.text,
                confidence=float(result.confidence),
                success=not result.degraded and not result.error_code,
                degraded=result.degraded,
                error_code=result.error_code,
                error_message=result.error_message,
                language=result.language or sample.language,
                audio_duration_sec=audio_duration_sec,
                preprocess_ms=float(result.latency.preprocess_ms),
                inference_ms=float(result.latency.inference_ms),
                postprocess_ms=float(result.latency.postprocess_ms),
                total_latency_ms=float(result.latency.total_ms),
                reference_text=sample.transcript,
                extra_metrics=metrics,
            )
            trace_artifact_ref = self.trace_exporter.export_benchmark_trace(
                run_dir=self.run_dir,
                trace=trace,
            )
            trace_corrupted = bool(trace.validation.corrupted)
            metrics["cpu_percent"] = trace.metrics.get("cpu_percent", 0.0)
            metrics["memory_mb"] = trace.metrics.get("memory_mb", 0.0)
            metrics["gpu_util_percent"] = trace.metrics.get("gpu_util_percent", 0.0)
            metrics["gpu_memory_mb"] = trace.metrics.get("gpu_memory_mb", 0.0)

        return {
            "run_id": run_id,
            "provider_profile": provider_profile,
            "provider_id": result.provider_id,
            "sample_id": sample.sample_id,
            "success": context.success,
            "text": result.text,
            "reference_text": sample.transcript,
            "normalized_reference_text": quality_support.normalized_reference,
            "normalized_hypothesis_text": quality_support.normalized_hypothesis,
            "quality_support": quality_support.as_dict(),
            "error_code": result.error_code,
            "error_message": result.error_message,
            "metrics": metrics,
            "execution_mode": execution_meta.get("execution_mode", "batch"),
            "streaming_mode": execution_meta.get("streaming_mode", "none"),
            "scenario": execution_meta.get("scenario", "clean_baseline"),
            "noise_level": execution_meta.get("noise_level", "clean"),
            "noise_mode": execution_meta.get("noise_mode", "none"),
            "noise_snr_db": execution_meta.get("snr_db"),
            "provider_preset": execution_meta.get("provider_preset", ""),
            "input_audio_path": active_audio_path,
            "audio_duration_sec": audio_duration_sec,
            "confidence": float(result.confidence),
            "preprocess_ms": float(result.latency.preprocess_ms),
            "inference_ms": float(result.latency.inference_ms),
            "postprocess_ms": float(result.latency.postprocess_ms),
            "trace_artifact_ref": trace_artifact_ref,
            "trace_corrupted": trace_corrupted,
            "normalized_result": result.as_dict(),
        }

    def run_sample_streaming(
        self,
        *,
        run_id: str,
        provider,
        provider_profile: str,
        sample: DatasetSample,
        session_id: str,
        sample_audio_path: str | None = None,
        execution_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        execution_meta = execution_meta or {}
        active_audio_path = str(sample_audio_path or sample.audio_path)
        audio_duration_sec = float(sample.duration_sec or 0.0)
        if audio_duration_sec <= 0.0:
            try:
                audio_duration_sec = float(wav_duration_sec(active_audio_path))
            except Exception:
                audio_duration_sec = 0.0

        sample_rate_hz, channels, sample_width_bytes, _ = wav_info(active_audio_path)
        chunk_ms = int(execution_meta.get("streaming_chunk_ms", 500) or 500)
        chunk_sec = max(float(chunk_ms) / 1000.0, 0.05)
        request_id = make_request_id()
        trace_collector = PipelineTraceCollector(
            trace_type="benchmark_stream_sample",
            request_id=request_id,
            session_id=session_id,
            run_id=run_id,
            provider_id=getattr(provider, "provider_id", ""),
            metadata={
                "provider_profile": provider_profile,
                "sample_id": sample.sample_id,
                "scenario": execution_meta.get("scenario", "clean_baseline"),
                "noise_level": execution_meta.get("noise_level", "clean"),
                "input_audio_path": active_audio_path,
                "streaming_mode": execution_meta.get("streaming_mode", "none"),
            },
        )

        partial_count = 0
        first_partial_latency_ms = 0.0
        start = perf_counter()
        replay_rate = self._stream_replay_rate(execution_meta)
        streamed_audio_sec = 0.0
        with trace_collector.stage(
            "provider_stream",
            component=getattr(provider, "provider_id", "provider"),
            code_path=f"{type(provider).__module__}.{type(provider).__name__}.start_stream",
            input_summary={
                "audio_duration_sec": audio_duration_sec,
                "language": sample.language,
                "provider_profile": provider_profile,
                "chunk_ms": chunk_ms,
            },
        ) as stage_output:
            provider.start_stream(
                {
                    "session_id": session_id,
                    "request_id": request_id,
                    "language": sample.language,
                    "sample_rate_hz": sample_rate_hz,
                    "channels": channels,
                    "encoding": "pcm_s16le"
                    if sample_width_bytes == 2
                    else f"pcm_s{sample_width_bytes * 8}le",
                    "sample_width_bytes": sample_width_bytes,
                }
            )
            for chunk in wav_pcm_chunks(active_audio_path, chunk_sec):
                updates = []
                partial = provider.push_audio(chunk)
                if partial is not None:
                    updates.append(partial)
                updates.extend(provider.drain_stream_results())
                for update in updates:
                    if not update.is_partial or not update.text:
                        continue
                    partial_count += 1
                    if first_partial_latency_ms <= 0.0:
                        first_partial_latency_ms = float(
                            update.latency.first_partial_ms or (perf_counter() - start) * 1000.0
                        )
                if replay_rate > 0.0:
                    bytes_per_second = max(
                        int(sample_rate_hz)
                        * max(int(channels), 1)
                        * max(int(sample_width_bytes), 1),
                        1,
                    )
                    streamed_audio_sec += len(chunk) / float(bytes_per_second)
                    target_elapsed_sec = streamed_audio_sec / replay_rate
                    remaining_sec = target_elapsed_sec - (perf_counter() - start)
                    if remaining_sec > 0.0:
                        sleep(remaining_sec)
            result = provider.stop_stream()
            for update in provider.drain_stream_results():
                if not update.is_partial or not update.text:
                    continue
                partial_count += 1
                if first_partial_latency_ms <= 0.0:
                    first_partial_latency_ms = float(
                        update.latency.first_partial_ms or (perf_counter() - start) * 1000.0
                    )
            stage_output["partial_count"] = partial_count
            stage_output["first_partial_latency_ms"] = first_partial_latency_ms
            stage_output["latency_ms"] = float(result.latency.total_ms)
            stage_output["provider_id"] = result.provider_id
            stage_output["text_length"] = len(str(result.text or ""))
        finalization_latency_ms = float(result.latency.finalization_ms or 0.0)
        estimated_cost_usd = float(execution_meta.get("estimated_cost_usd", 0.0) or 0.0)
        self._require_quality_reference(sample)
        quality_support = text_quality_support(sample.transcript, result.text)

        context = MetricContext(
            reference_text=sample.transcript,
            hypothesis_text=result.text,
            latency_ms=result.latency.total_ms,
            success=not result.degraded and not result.error_code,
            execution_mode="streaming",
            audio_duration_sec=audio_duration_sec,
            estimated_cost_usd=estimated_cost_usd,
            first_partial_latency_ms=first_partial_latency_ms,
            finalization_latency_ms=finalization_latency_ms,
            partial_count=partial_count,
            quality_support=quality_support,
        )
        metrics = self.metric_engine.evaluate(context)
        metrics["confidence"] = float(result.confidence)
        metrics["preprocess_ms"] = float(result.latency.preprocess_ms)
        metrics["inference_ms"] = float(result.latency.inference_ms)
        metrics["postprocess_ms"] = float(result.latency.postprocess_ms)
        trace_artifact_ref = ""
        trace_corrupted = False
        if self.observability_config is not None and self.trace_exporter is not None and self.run_dir:
            trace_collector.set_metric("first_partial_latency_ms", first_partial_latency_ms)
            trace_collector.set_metric("finalization_latency_ms", finalization_latency_ms)
            trace_collector.set_metric("partial_count", partial_count)
            trace = build_benchmark_trace(
                collector=trace_collector,
                config=self.observability_config,
                provider_id=result.provider_id,
                text=result.text,
                confidence=float(result.confidence),
                success=not result.degraded and not result.error_code,
                degraded=result.degraded,
                error_code=result.error_code,
                error_message=result.error_message,
                language=result.language or sample.language,
                audio_duration_sec=audio_duration_sec,
                preprocess_ms=float(result.latency.preprocess_ms),
                inference_ms=float(result.latency.inference_ms),
                postprocess_ms=float(result.latency.postprocess_ms),
                total_latency_ms=float(result.latency.total_ms),
                reference_text=sample.transcript,
                extra_metrics=metrics,
            )
            trace_artifact_ref = self.trace_exporter.export_benchmark_trace(
                run_dir=self.run_dir,
                trace=trace,
            )
            trace_corrupted = bool(trace.validation.corrupted)
            metrics["cpu_percent"] = trace.metrics.get("cpu_percent", 0.0)
            metrics["memory_mb"] = trace.metrics.get("memory_mb", 0.0)
            metrics["gpu_util_percent"] = trace.metrics.get("gpu_util_percent", 0.0)
            metrics["gpu_memory_mb"] = trace.metrics.get("gpu_memory_mb", 0.0)

        return {
            "run_id": run_id,
            "provider_profile": provider_profile,
            "provider_id": result.provider_id,
            "sample_id": sample.sample_id,
            "success": context.success,
            "text": result.text,
            "reference_text": sample.transcript,
            "normalized_reference_text": quality_support.normalized_reference,
            "normalized_hypothesis_text": quality_support.normalized_hypothesis,
            "quality_support": quality_support.as_dict(),
            "error_code": result.error_code,
            "error_message": result.error_message,
            "metrics": metrics,
            "execution_mode": "streaming",
            "streaming_mode": execution_meta.get("streaming_mode", "none"),
            "scenario": execution_meta.get("scenario", "clean_baseline"),
            "noise_level": execution_meta.get("noise_level", "clean"),
            "noise_mode": execution_meta.get("noise_mode", "none"),
            "noise_snr_db": execution_meta.get("snr_db"),
            "provider_preset": execution_meta.get("provider_preset", ""),
            "input_audio_path": active_audio_path,
            "audio_duration_sec": audio_duration_sec,
            "partial_count": partial_count,
            "first_partial_latency_ms": first_partial_latency_ms,
            "finalization_latency_ms": finalization_latency_ms,
            "confidence": float(result.confidence),
            "preprocess_ms": float(result.latency.preprocess_ms),
            "inference_ms": float(result.latency.inference_ms),
            "postprocess_ms": float(result.latency.postprocess_ms),
            "trace_artifact_ref": trace_artifact_ref,
            "trace_corrupted": trace_corrupted,
            "normalized_result": result.as_dict(),
        }
