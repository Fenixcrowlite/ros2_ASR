"""Batch executor for benchmark sample x provider matrix.

The orchestrator owns *what* should be executed; this module owns *how* one
provider is run against one sample, both for batch and streaming benchmark
paths.
"""

from __future__ import annotations

from time import perf_counter, sleep
from typing import Any

from asr_core import make_request_id
from asr_core.audio import wav_duration_sec, wav_info, wav_pcm_chunks
from asr_datasets import DatasetSample
from asr_metrics.engine import MetricEngine
from asr_metrics.plugins import MetricContext
from asr_metrics.quality import require_quality_reference, text_quality_support
from asr_metrics.semantics import (
    METRICS_SEMANTICS_VERSION,
    apply_legacy_metric_aliases,
    resolve_audio_duration_fields,
)
from asr_metrics.system import ResourceSampler
from asr_observability import (
    FileTraceExporter,
    ObservabilityConfig,
    PipelineTraceCollector,
    build_benchmark_trace,
)
from asr_provider_base import ProviderAudio, provider_runtime_metadata


class BatchExecutor:
    """Execute one resolved benchmark sample/provider unit of work."""

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

    @staticmethod
    def _duration_fields(sample: DatasetSample, active_audio_path: str) -> dict[str, Any]:
        declared_audio_duration_sec = float(sample.duration_sec or 0.0) or None
        measured_audio_duration_sec: float | None = None
        try:
            measured_audio_duration_sec = float(wav_duration_sec(active_audio_path))
        except Exception:
            measured_audio_duration_sec = None
        duration_fields = resolve_audio_duration_fields(
            measured_audio_duration_sec=measured_audio_duration_sec,
            declared_audio_duration_sec=declared_audio_duration_sec,
        )
        duration_fields["audio_duration_source"] = (
            "measured_file"
            if duration_fields.get("measured_audio_duration_sec") not in (None, 0.0)
            else "manifest_declared"
        )
        return duration_fields

    @staticmethod
    def _estimated_cost_usd(
        duration_fields: dict[str, Any],
        execution_meta: dict[str, Any],
    ) -> float:
        provider_cost_per_minute = float(
            execution_meta.get("estimated_cost_usd_per_min", 0.0)
            or execution_meta.get("provider_cost_per_minute_usd", 0.0)
            or 0.0
        )
        if provider_cost_per_minute <= 0.0:
            return float(execution_meta.get("estimated_cost_usd", 0.0) or 0.0)
        effective_duration_sec = float(duration_fields.get("audio_duration_sec", 0.0) or 0.0)
        return (effective_duration_sec / 60.0) * provider_cost_per_minute

    @staticmethod
    def _trace_resource_metrics(trace: Any) -> dict[str, float]:
        metrics: dict[str, float] = {}
        for key in (
            "cpu_percent_mean",
            "cpu_percent_peak",
            "memory_mb_mean",
            "memory_mb_peak",
            "gpu_util_percent_mean",
            "gpu_util_percent_peak",
            "gpu_memory_mb_mean",
            "gpu_memory_mb_peak",
            "cpu_percent",
            "memory_mb",
            "gpu_util_percent",
            "gpu_memory_mb",
        ):
            value = trace.metrics.get(key)
            if value is None:
                continue
            metrics[key] = float(value)
        return metrics

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

    @staticmethod
    def _populate_metric_envelope(
        metrics: dict[str, Any],
        *,
        duration_fields: dict[str, Any],
        provider_compute_latency_ms: float,
        end_to_end_latency_ms: float,
        time_to_first_result_ms: float,
        time_to_final_result_ms: float,
        finalization_latency_ms: float | None,
        estimated_cost_usd: float,
        partial_count: int = 0,
        first_partial_latency_ms: float = 0.0,
    ) -> dict[str, Any]:
        metrics.update(duration_fields)
        metrics["provider_compute_latency_ms"] = float(provider_compute_latency_ms)
        metrics["end_to_end_latency_ms"] = float(end_to_end_latency_ms)
        metrics["time_to_first_result_ms"] = float(time_to_first_result_ms)
        metrics["time_to_final_result_ms"] = float(time_to_final_result_ms)
        metrics["estimated_cost_usd"] = float(estimated_cost_usd)
        metrics["partial_count"] = int(partial_count)
        metrics["first_partial_latency_ms"] = float(first_partial_latency_ms)
        if finalization_latency_ms is not None:
            metrics["finalization_latency_ms"] = float(finalization_latency_ms)
        return apply_legacy_metric_aliases(metrics)

    @staticmethod
    def _trace_fields(trace) -> dict[str, Any]:
        return {
            "trace_artifact_ref": trace.artifact_path,
            "trace_corrupted": bool(trace.validation.corrupted),
            "trace_warnings": list(trace.validation.warnings),
            "trace_warning_count": len(trace.validation.warnings),
        }

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
        # Batch mode is the simplest benchmark path: one WAV file goes into one
        # provider request and produces one normalized result row.
        execution_meta = execution_meta or {}
        active_audio_path = str(sample_audio_path or sample.audio_path)
        duration_fields = self._duration_fields(sample, active_audio_path)
        audio_duration_sec = float(duration_fields.get("audio_duration_sec", 0.0) or 0.0)

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
        provider_meta = provider_runtime_metadata(provider, record_invocation=True)
        resource_sampler = ResourceSampler() if self.observability_config is not None else None
        execution_started_at = perf_counter()
        if resource_sampler is not None:
            resource_sampler.start()
        try:
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
            end_to_end_latency_ms = max(
                (perf_counter() - execution_started_at) * 1000.0,
                float(result.latency.total_ms),
                0.0,
            )
        finally:
            resource_sample = resource_sampler.stop() if resource_sampler is not None else None

        # Metrics are computed from the normalized provider result plus the
        # benchmark-side timing/duration envelope gathered around the call.
        estimated_cost_usd = self._estimated_cost_usd(duration_fields, execution_meta)
        self._require_quality_reference(sample)
        quality_support = text_quality_support(sample.transcript, result.text)
        context = MetricContext(
            reference_text=sample.transcript,
            hypothesis_text=result.text,
            success=not result.degraded and not result.error_code,
            execution_mode=str(execution_meta.get("execution_mode", "batch") or "batch"),
            provider_compute_latency_ms=float(result.latency.total_ms),
            end_to_end_latency_ms=end_to_end_latency_ms,
            measured_audio_duration_sec=float(
                duration_fields.get("audio_duration_sec", 0.0) or 0.0
            ),
            estimated_cost_usd=estimated_cost_usd,
            time_to_first_result_ms=end_to_end_latency_ms,
            time_to_final_result_ms=end_to_end_latency_ms,
            quality_support=quality_support,
        )
        metrics = self.metric_engine.evaluate(context)
        metrics["confidence"] = float(result.confidence)
        metrics["preprocess_ms"] = float(result.latency.preprocess_ms)
        metrics["inference_ms"] = float(result.latency.inference_ms)
        metrics["postprocess_ms"] = float(result.latency.postprocess_ms)
        metrics.update(provider_meta)
        self._populate_metric_envelope(
            metrics,
            duration_fields=duration_fields,
            provider_compute_latency_ms=float(result.latency.total_ms),
            end_to_end_latency_ms=end_to_end_latency_ms,
            time_to_first_result_ms=end_to_end_latency_ms,
            time_to_final_result_ms=end_to_end_latency_ms,
            finalization_latency_ms=None,
            estimated_cost_usd=estimated_cost_usd,
        )

        trace_artifact_ref = ""
        trace_corrupted = False
        trace_warnings: list[str] = []
        if (
            self.observability_config is not None
            and self.trace_exporter is not None
            and self.run_dir
        ):
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
                measured_audio_duration_sec=duration_fields.get("measured_audio_duration_sec"),
                declared_audio_duration_sec=duration_fields.get("declared_audio_duration_sec"),
                preprocess_ms=float(result.latency.preprocess_ms),
                inference_ms=float(result.latency.inference_ms),
                postprocess_ms=float(result.latency.postprocess_ms),
                provider_compute_latency_ms=float(result.latency.total_ms),
                end_to_end_latency_ms=end_to_end_latency_ms,
                time_to_first_result_ms=end_to_end_latency_ms,
                time_to_final_result_ms=end_to_end_latency_ms,
                resource_sample=resource_sample,
                audio_duration_source=str(duration_fields.get("audio_duration_source", "")),
                reference_text=sample.transcript,
                extra_metrics=metrics,
            )
            trace_artifact_ref = self.trace_exporter.export_benchmark_trace(
                run_dir=self.run_dir,
                trace=trace,
            )
            trace_fields = self._trace_fields(trace)
            trace_corrupted = bool(trace_fields["trace_corrupted"])
            trace_warnings = list(trace_fields["trace_warnings"])
            metrics.update(self._trace_resource_metrics(trace))

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
            "metrics_semantics_version": METRICS_SEMANTICS_VERSION,
            "legacy_metrics": False,
            "execution_mode": execution_meta.get("execution_mode", "batch"),
            "streaming_mode": execution_meta.get("streaming_mode", "none"),
            "scenario": execution_meta.get("scenario", "clean_baseline"),
            "noise_level": execution_meta.get("noise_level", "clean"),
            "noise_mode": execution_meta.get("noise_mode", "none"),
            "noise_snr_db": execution_meta.get("snr_db"),
            "provider_preset": execution_meta.get("provider_preset", ""),
            "input_audio_path": active_audio_path,
            "audio_duration_sec": audio_duration_sec,
            "measured_audio_duration_sec": duration_fields.get("measured_audio_duration_sec"),
            "declared_audio_duration_sec": duration_fields.get("declared_audio_duration_sec"),
            "duration_mismatch_sec": duration_fields.get("duration_mismatch_sec"),
            "audio_duration_source": duration_fields.get("audio_duration_source"),
            "confidence": float(result.confidence),
            "preprocess_ms": float(result.latency.preprocess_ms),
            "inference_ms": float(result.latency.inference_ms),
            "postprocess_ms": float(result.latency.postprocess_ms),
            "trace_artifact_ref": trace_artifact_ref,
            "trace_corrupted": trace_corrupted,
            "trace_warnings": trace_warnings,
            "trace_warning_count": len(trace_warnings),
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
        # Streaming mode replays one WAV as deterministic PCM chunks and asks
        # the provider to behave as if it were serving a live stream.
        execution_meta = execution_meta or {}
        active_audio_path = str(sample_audio_path or sample.audio_path)
        duration_fields = self._duration_fields(sample, active_audio_path)
        audio_duration_sec = float(duration_fields.get("audio_duration_sec", 0.0) or 0.0)

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
        provider_meta = provider_runtime_metadata(provider, record_invocation=True)

        partial_count = 0
        seen_partial_texts: set[str] = set()
        first_partial_latency_ms = 0.0
        start = perf_counter()
        replay_rate = self._stream_replay_rate(execution_meta)
        streamed_audio_sec = 0.0
        stop_requested_at = 0.0
        resource_sampler = ResourceSampler() if self.observability_config is not None else None
        if resource_sampler is not None:
            resource_sampler.start()
        try:
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
                    # Partial handling intentionally deduplicates repeated text
                    # because many providers resend the same hypothesis as the
                    # stream stabilizes.
                    updates = []
                    partial = provider.push_audio(chunk)
                    if partial is not None:
                        updates.append(partial)
                    updates.extend(provider.drain_stream_results())
                    for update in updates:
                        if not update.is_partial or not update.text:
                            continue
                        partial_text = str(update.text or "").strip()
                        if not partial_text or partial_text in seen_partial_texts:
                            continue
                        seen_partial_texts.add(partial_text)
                        partial_count += 1
                        if first_partial_latency_ms <= 0.0:
                            first_partial_latency_ms = max(
                                float(update.latency.first_partial_ms or 0.0),
                                (perf_counter() - start) * 1000.0,
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
                stop_requested_at = perf_counter()
                result = provider.stop_stream()
                for update in provider.drain_stream_results():
                    if not update.is_partial or not update.text:
                        continue
                    partial_text = str(update.text or "").strip()
                    if not partial_text or partial_text in seen_partial_texts:
                        continue
                    seen_partial_texts.add(partial_text)
                    partial_count += 1
                    if first_partial_latency_ms <= 0.0:
                        first_partial_latency_ms = max(
                            float(update.latency.first_partial_ms or 0.0),
                            (perf_counter() - start) * 1000.0,
                        )
                stage_output["partial_count"] = partial_count
                stage_output["first_partial_latency_ms"] = first_partial_latency_ms
                stage_output["latency_ms"] = float(result.latency.total_ms)
                stage_output["provider_id"] = result.provider_id
                stage_output["text_length"] = len(str(result.text or ""))
            end_to_end_latency_ms = max(
                (perf_counter() - start) * 1000.0,
                float(result.latency.total_ms),
                0.0,
            )
        finally:
            resource_sample = resource_sampler.stop() if resource_sampler is not None else None

        if first_partial_latency_ms <= 0.0:
            first_partial_latency_ms = end_to_end_latency_ms
        provider_first_partial_ms = float(result.latency.first_partial_ms or 0.0)
        time_to_first_result_ms = max(first_partial_latency_ms, provider_first_partial_ms)
        time_to_final_result_ms = end_to_end_latency_ms
        finalization_latency_ms = (
            max((perf_counter() - stop_requested_at) * 1000.0, 0.0)
            if stop_requested_at > 0.0
            else 0.0
        )
        estimated_cost_usd = self._estimated_cost_usd(duration_fields, execution_meta)
        self._require_quality_reference(sample)
        quality_support = text_quality_support(sample.transcript, result.text)

        context = MetricContext(
            reference_text=sample.transcript,
            hypothesis_text=result.text,
            success=not result.degraded and not result.error_code,
            execution_mode="streaming",
            provider_compute_latency_ms=float(result.latency.total_ms),
            end_to_end_latency_ms=end_to_end_latency_ms,
            measured_audio_duration_sec=float(
                duration_fields.get("audio_duration_sec", 0.0) or 0.0
            ),
            estimated_cost_usd=estimated_cost_usd,
            first_partial_latency_ms=float(
                result.latency.first_partial_ms or first_partial_latency_ms
            ),
            time_to_first_result_ms=time_to_first_result_ms,
            time_to_final_result_ms=time_to_final_result_ms,
            finalization_latency_ms=finalization_latency_ms,
            partial_count=partial_count,
            quality_support=quality_support,
        )
        metrics = self.metric_engine.evaluate(context)
        metrics["confidence"] = float(result.confidence)
        metrics["preprocess_ms"] = float(result.latency.preprocess_ms)
        metrics["inference_ms"] = float(result.latency.inference_ms)
        metrics["postprocess_ms"] = float(result.latency.postprocess_ms)
        metrics.update(provider_meta)
        self._populate_metric_envelope(
            metrics,
            duration_fields=duration_fields,
            provider_compute_latency_ms=float(result.latency.total_ms),
            end_to_end_latency_ms=end_to_end_latency_ms,
            time_to_first_result_ms=time_to_first_result_ms,
            time_to_final_result_ms=time_to_final_result_ms,
            finalization_latency_ms=finalization_latency_ms,
            estimated_cost_usd=estimated_cost_usd,
            partial_count=partial_count,
            first_partial_latency_ms=float(
                result.latency.first_partial_ms or first_partial_latency_ms
            ),
        )

        trace_artifact_ref = ""
        trace_corrupted = False
        trace_warnings: list[str] = []
        if (
            self.observability_config is not None
            and self.trace_exporter is not None
            and self.run_dir
        ):
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
                measured_audio_duration_sec=duration_fields.get("measured_audio_duration_sec"),
                declared_audio_duration_sec=duration_fields.get("declared_audio_duration_sec"),
                preprocess_ms=float(result.latency.preprocess_ms),
                inference_ms=float(result.latency.inference_ms),
                postprocess_ms=float(result.latency.postprocess_ms),
                provider_compute_latency_ms=float(result.latency.total_ms),
                end_to_end_latency_ms=end_to_end_latency_ms,
                time_to_first_result_ms=time_to_first_result_ms,
                time_to_final_result_ms=time_to_final_result_ms,
                finalization_latency_ms=finalization_latency_ms,
                resource_sample=resource_sample,
                audio_duration_source=str(duration_fields.get("audio_duration_source", "")),
                reference_text=sample.transcript,
                extra_metrics=metrics,
            )
            trace_artifact_ref = self.trace_exporter.export_benchmark_trace(
                run_dir=self.run_dir,
                trace=trace,
            )
            trace_fields = self._trace_fields(trace)
            trace_corrupted = bool(trace_fields["trace_corrupted"])
            trace_warnings = list(trace_fields["trace_warnings"])
            metrics.update(self._trace_resource_metrics(trace))

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
            "metrics_semantics_version": METRICS_SEMANTICS_VERSION,
            "legacy_metrics": False,
            "execution_mode": "streaming",
            "streaming_mode": execution_meta.get("streaming_mode", "none"),
            "scenario": execution_meta.get("scenario", "clean_baseline"),
            "noise_level": execution_meta.get("noise_level", "clean"),
            "noise_mode": execution_meta.get("noise_mode", "none"),
            "noise_snr_db": execution_meta.get("snr_db"),
            "provider_preset": execution_meta.get("provider_preset", ""),
            "input_audio_path": active_audio_path,
            "audio_duration_sec": audio_duration_sec,
            "measured_audio_duration_sec": duration_fields.get("measured_audio_duration_sec"),
            "declared_audio_duration_sec": duration_fields.get("declared_audio_duration_sec"),
            "duration_mismatch_sec": duration_fields.get("duration_mismatch_sec"),
            "audio_duration_source": duration_fields.get("audio_duration_source"),
            "partial_count": partial_count,
            "first_partial_latency_ms": float(
                result.latency.first_partial_ms or first_partial_latency_ms
            ),
            "finalization_latency_ms": finalization_latency_ms,
            "confidence": float(result.confidence),
            "preprocess_ms": float(result.latency.preprocess_ms),
            "inference_ms": float(result.latency.inference_ms),
            "postprocess_ms": float(result.latency.postprocess_ms),
            "trace_artifact_ref": trace_artifact_ref,
            "trace_corrupted": trace_corrupted,
            "trace_warnings": trace_warnings,
            "trace_warning_count": len(trace_warnings),
            "normalized_result": result.as_dict(),
        }
