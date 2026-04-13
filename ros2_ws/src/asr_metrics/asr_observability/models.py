"""Shared models for pipeline tracing and observability exports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from asr_metrics.semantics import METRICS_SEMANTICS_VERSION


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class StageTrace:
    """One timed stage inside a runtime or benchmark pipeline trace."""

    stage: str
    component: str
    code_path: str
    started_ns: int
    ended_ns: int
    duration_ms: float
    wall_started_at: str
    wall_finished_at: str
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Serialize the stage trace into a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    """Validation outcome attached to an exported pipeline trace."""

    valid: bool = True
    corrupted: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the validation report into a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class PipelineTrace:
    """Full observability trace for one runtime request or benchmark execution."""

    trace_id: str
    trace_type: str
    created_at: str
    metrics_semantics_version: int = METRICS_SEMANTICS_VERSION
    legacy_metrics: bool = False
    request_id: str = ""
    session_id: str = ""
    run_id: str = ""
    provider_id: str = ""
    started_ns: int = 0
    finished_ns: int = 0
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    stages: list[StageTrace] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    validation: ValidationReport = field(default_factory=ValidationReport)
    artifact_path: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Serialize nested trace data into a JSON-friendly dictionary."""
        payload = asdict(self)
        payload["stages"] = [stage.as_dict() for stage in self.stages]
        payload["validation"] = self.validation.as_dict()
        return payload
