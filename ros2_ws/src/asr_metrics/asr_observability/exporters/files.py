"""JSON/CSV exporters for runtime and benchmark traces."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from asr_observability.config import ObservabilityConfig
from asr_observability.models import PipelineTrace


class FileTraceExporter:
    def __init__(self, config: ObservabilityConfig) -> None:
        self.config = config

    def runtime_trace_path(self, trace: PipelineTrace) -> Path:
        return (
            Path(self.config.artifact_root)
            / "runtime_sessions"
            / (trace.session_id or "unknown_session")
            / "metrics"
            / f"{trace.trace_id}.json"
        )

    @staticmethod
    def benchmark_trace_path(*, run_dir: str, trace: PipelineTrace) -> Path:
        return Path(run_dir) / "metrics" / "traces" / f"{trace.trace_id}.json"

    def _append_csv_row(self, path: Path, row: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists()
        fieldnames = list(row.keys())
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    @staticmethod
    def _summary_row(trace: PipelineTrace) -> dict[str, Any]:
        return {
            "trace_id": trace.trace_id,
            "trace_type": trace.trace_type,
            "created_at": trace.created_at,
            "request_id": trace.request_id,
            "session_id": trace.session_id,
            "run_id": trace.run_id,
            "provider_id": trace.provider_id,
            "total_duration_ms": trace.total_duration_ms,
            "total_latency_ms": trace.metrics.get("total_latency_ms", 0.0),
            "preprocess_ms": trace.metrics.get("preprocess_ms", 0.0),
            "inference_ms": trace.metrics.get("inference_ms", 0.0),
            "postprocess_ms": trace.metrics.get("postprocess_ms", 0.0),
            "audio_load_ms": trace.metrics.get("audio_load_ms", 0.0),
            "ros_service_latency_ms": trace.metrics.get("ros_service_latency_ms", 0.0),
            "time_to_result_ms": trace.metrics.get("time_to_result_ms", 0.0),
            "real_time_factor": trace.metrics.get("real_time_factor", 0.0),
            "model_load_ms": trace.metrics.get("model_load_ms", ""),
            "provider_init_cold_start": trace.metrics.get("provider_init_cold_start", ""),
            "provider_call_cold_start": trace.metrics.get("provider_call_cold_start", ""),
            "provider_invocation_index": trace.metrics.get("provider_invocation_index", ""),
            "time_to_first_result_ms": trace.metrics.get("time_to_first_result_ms", ""),
            "time_to_final_result_ms": trace.metrics.get("time_to_final_result_ms", ""),
            "topic_delivery_ms": trace.metrics.get("topic_delivery_ms", ""),
            "max_topic_delivery_ms": trace.metrics.get("max_topic_delivery_ms", ""),
            "sequence_gap_count": trace.metrics.get("sequence_gap_count", ""),
            "chunk_count": trace.metrics.get("chunk_count", ""),
            "wer": trace.metrics.get("wer", ""),
            "cer": trace.metrics.get("cer", ""),
            "confidence": trace.metrics.get("confidence", ""),
            "cpu_percent": trace.metrics.get("cpu_percent", ""),
            "memory_mb": trace.metrics.get("memory_mb", ""),
            "gpu_util_percent": trace.metrics.get("gpu_util_percent", ""),
            "gpu_memory_mb": trace.metrics.get("gpu_memory_mb", ""),
            "success": trace.metrics.get("success", ""),
            "degraded": trace.metrics.get("degraded", ""),
            "error_code": trace.metrics.get("error_code", ""),
            "corrupted": trace.validation.corrupted,
            "artifact_path": trace.artifact_path,
        }

    def export_runtime_trace(self, trace: PipelineTrace) -> str:
        json_path = self.runtime_trace_path(trace)
        base_dir = json_path.parent
        base_dir.mkdir(parents=True, exist_ok=True)
        trace.artifact_path = str(json_path)
        if self.config.export_json:
            json_path.write_text(
                json.dumps(trace.as_dict(), ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
        if self.config.export_csv:
            self._append_csv_row(
                base_dir / self.config.runtime_index_filename,
                self._summary_row(trace),
            )
        return str(json_path)

    def export_benchmark_trace(self, *, run_dir: str, trace: PipelineTrace) -> str:
        json_path = self.benchmark_trace_path(run_dir=run_dir, trace=trace)
        base_dir = json_path.parent
        base_dir.mkdir(parents=True, exist_ok=True)
        trace.artifact_path = str(json_path)
        if self.config.export_json:
            json_path.write_text(
                json.dumps(trace.as_dict(), ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
        if self.config.export_csv:
            self._append_csv_row(
                base_dir / self.config.benchmark_index_filename,
                self._summary_row(trace),
            )
        return str(json_path)
