"""Benchmark core models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BenchmarkRunRequest:
    benchmark_profile: str
    dataset_profile: str = ""
    providers: list[str] = field(default_factory=list)
    scenario: str = ""
    provider_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    benchmark_settings: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""


@dataclass(slots=True)
class BenchmarkSampleResult:
    run_id: str
    provider_profile: str
    sample_id: str
    success: bool
    text: str
    error_code: str
    error_message: str
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkRunSummary:
    run_id: str
    benchmark_profile: str
    dataset_id: str
    providers: list[str]
    total_samples: int
    successful_samples: int
    failed_samples: int
    mean_metrics: dict[str, float] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
