from __future__ import annotations

import importlib
import sys
import types

import asr_benchmark_core.executor as benchmark_executor_module
import asr_benchmark_core.orchestrator as benchmark_orchestrator_module
import asr_runtime_nodes.asr_orchestrator_node as runtime_orchestrator_module


def test_orchestrator_imports_do_not_depend_on_global_metrics_package(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "metrics", types.ModuleType("metrics"))
    importlib.reload(benchmark_executor_module)
    benchmark_module = importlib.reload(benchmark_orchestrator_module)
    runtime_module = importlib.reload(runtime_orchestrator_module)

    assert benchmark_module.BenchmarkOrchestrator.__name__ == "BenchmarkOrchestrator"
    assert runtime_module.AsrOrchestratorNode.__name__ == "AsrOrchestratorNode"
