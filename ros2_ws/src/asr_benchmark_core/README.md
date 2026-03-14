# asr_benchmark_core

Benchmark orchestration core.

## Responsibilities
- Resolve benchmark/dataset/provider/metric profiles.
- Execute provider x sample matrix.
- Compute metrics via plugin engine.
- Persist reproducible run artifacts and summary.

## Boundaries
- No GUI/API exposure (use `asr_benchmark_nodes` / `asr_gateway`).
