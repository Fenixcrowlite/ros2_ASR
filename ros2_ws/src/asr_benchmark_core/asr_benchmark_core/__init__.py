"""Benchmark core package."""

from asr_benchmark_core.models import BenchmarkRunRequest, BenchmarkRunSummary

__all__ = ["BenchmarkRunRequest", "BenchmarkRunSummary", "BenchmarkOrchestrator"]


def __getattr__(name: str):
    if name == "BenchmarkOrchestrator":
        from asr_benchmark_core.orchestrator import BenchmarkOrchestrator

        return BenchmarkOrchestrator
    raise AttributeError(f"module 'asr_benchmark_core' has no attribute {name!r}")
