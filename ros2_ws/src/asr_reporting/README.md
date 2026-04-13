# asr_reporting

Small export layer for benchmark result payloads and report artifacts.

## Purpose

This package keeps report file emission simple and reusable. It does not decide
what the benchmark summary should contain; it only writes already-prepared data
to JSON, CSV, and Markdown outputs.

## Main Responsibilities

- Export JSON payloads with stable formatting.
- Export flat row collections to CSV.
- Export simple Markdown bullet summaries.

## Key Module

- `asr_reporting/exporter.py`: `export_json`, `export_csv`, and
  `export_markdown`.

## Typical Callers

- `asr_benchmark_core` when persisting run summaries.
- `asr_gateway` when building downloadable report files.

## Boundary Rules

- No metric computation.
- No artifact directory ownership.
- No dataset or provider logic.
