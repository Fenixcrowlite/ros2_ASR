# asr_metrics

Metric engine, quality scoring, resource sampling, and observability helpers
for ASR runtime and benchmark evaluation.

## Purpose

This package answers two different questions:

1. How good was the transcription?
2. How expensive or slow was it to produce?

It covers text quality metrics, latency/RTF/cost metrics, system resource
sampling, corpus-level summaries, and a lightweight observability model for
runtime and benchmark traces.

## Main Responsibilities

- Compute WER/CER and exact-match style quality metrics.
- Compute latency, real-time factor, partial-result, success, and cost metrics.
- Expose a plugin-style metric registry used by benchmark execution.
- Summarize per-sample rows into run-level aggregates for reports and UI.
- Collect CPU/RAM/GPU samples during runtime and benchmark execution.
- Build and validate observability traces for deeper troubleshooting.

## Key Modules

- `asr_metrics/plugins.py`: metric plugin classes and `MetricContext`.
- `asr_metrics/definitions.py`: metric catalog metadata and validation rules.
- `asr_metrics/engine.py`: evaluates configured metrics for one execution.
- `asr_metrics/quality.py`: text normalization, WER/CER support, and quality
  helpers.
- `asr_metrics/summary.py`: reduce many sample rows into report-ready summary
  sections.
- `asr_metrics/system.py`: resource sampling helpers for CPU, RAM, and GPU.
- `asr_metrics/semantics.py`: compatibility helpers for legacy vs canonical
  metric payload names.
- `asr_observability/*`: trace models, collectors, validators, and file export.

## Mental Model

- `MetricContext` is the normalized input to metric computation.
- `MetricEngine` turns that context into a flat metric dictionary.
- `summary.py` converts many flat dictionaries into a run overview.
- `system.py` and `asr_observability` provide operational visibility alongside
  quality metrics.

## Consumers

- `asr_benchmark_core` computes benchmark metrics and summaries here.
- `asr_runtime_nodes` and `asr_ros` use resource samplers/collectors.
- `asr_gateway` reads metric metadata and benchmark summaries for the UI.
- `asr_reporting` exports the aggregated results.

## Read This Package In This Order

1. `asr_metrics/definitions.py`
2. `asr_metrics/plugins.py`
3. `asr_metrics/engine.py`
4. `asr_metrics/quality.py`
5. `asr_metrics/summary.py`
6. `asr_metrics/system.py`
7. `asr_metrics/semantics.py`
