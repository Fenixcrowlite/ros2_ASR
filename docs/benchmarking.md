# Benchmarking

## Canonical Entry Point

- Local default: `make bench`
- Direct script: `python3 scripts/run_benchmark_core.py`

## Source Of Truth

- Canonical benchmark artifacts live under `artifacts/benchmark_runs/<run_id>/`.
- `results/latest_benchmark_summary.json` is the local summary pointer used by reporting/UI flows.
- `results/benchmark_results.json` and `results/benchmark_results.csv` are temporary derived compatibility exports generated from canonical run artifacts.

## Expected Outputs

- `manifest/run_manifest.json`
- `metrics/results.json`
- `metrics/results.csv`
- `reports/summary.json`
- `reports/summary.md`
- local pointers in `results/`

## Rules

- Benchmarks select providers only through provider profiles.
- Reports should read canonical summary artifacts, not archived legacy schemas as the primary source.
