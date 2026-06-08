"""High-resolution pipeline trace collector."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from asr_observability.models import PipelineTrace, StageTrace, utc_now_iso


class PipelineTraceCollector:
    """Collect high-resolution timing and metadata for one pipeline execution."""

    def __init__(
        self,
        *,
        trace_type: str,
        request_id: str = "",
        session_id: str = "",
        run_id: str = "",
        provider_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._started_ns = time.perf_counter_ns()
        self._trace = PipelineTrace(
            trace_id=f"trace_{uuid.uuid4().hex}",
            trace_type=trace_type,
            created_at=utc_now_iso(),
            request_id=request_id,
            session_id=session_id,
            run_id=run_id,
            provider_id=provider_id,
            started_ns=self._started_ns,
            metadata=dict(metadata or {}),
        )

    @property
    def trace(self) -> PipelineTrace:
        """Expose the mutable trace object being built."""
        return self._trace

    @contextmanager
    def stage(
        self,
        stage: str,
        *,
        component: str,
        code_path: str,
        input_summary: dict[str, Any] | None = None,
        notes: str = "",
    ) -> Iterator[dict[str, Any]]:
        """Context manager that records one timed stage and its output summary."""
        started_ns = time.perf_counter_ns()
        wall_started_at = utc_now_iso()
        output_summary: dict[str, Any] = {}
        try:
            yield output_summary
        finally:
            finished_ns = time.perf_counter_ns()
            self._trace.stages.append(
                StageTrace(
                    stage=stage,
                    component=component,
                    code_path=code_path,
                    started_ns=started_ns,
                    ended_ns=finished_ns,
                    duration_ms=max((finished_ns - started_ns) / 1_000_000.0, 0.0),
                    wall_started_at=wall_started_at,
                    wall_finished_at=utc_now_iso(),
                    input_summary=dict(input_summary or {}),
                    output_summary=dict(output_summary),
                    notes=notes,
                )
            )

    def set_metric(self, name: str, value: Any) -> None:
        """Attach one metric value to the trace."""
        self._trace.metrics[str(name)] = value

    def update_metadata(self, **kwargs: Any) -> None:
        """Merge non-null metadata keys into the trace header."""
        for key, value in kwargs.items():
            if value is None:
                continue
            self._trace.metadata[str(key)] = value

    def finalize(self) -> PipelineTrace:
        """Seal the trace with total duration and return it."""
        if self._trace.finished_ns > 0:
            return self._trace
        finished_ns = time.perf_counter_ns()
        self._trace.finished_ns = finished_ns
        self._trace.total_duration_ms = max((finished_ns - self._started_ns) / 1_000_000.0, 0.0)
        return self._trace
