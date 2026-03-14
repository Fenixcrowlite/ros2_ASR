# Storage and Artifacts Model

## Roots
- Runtime sessions: `artifacts/runtime_sessions/<session_id>/...`
- Benchmark runs: `artifacts/benchmark_runs/<run_id>/...`
- Comparisons: `artifacts/comparisons/...`
- Exports: `artifacts/exports/...`

## Runtime session structure
- `raw/`
- `normalized/`
- `metrics/`
- `logs/`

## Benchmark run structure
- `manifest/run_manifest.json`
- `resolved_configs/`
- `raw_outputs/*.json`
- `normalized_outputs/*.json`
- `metrics/results.json`, `metrics/results.csv`
- `reports/summary.json`, `reports/summary.md`
- `logs/`

## Persistence utilities
`asr_storage.ArtifactStore` handles:
- root management,
- deterministic run/session folder creation,
- manifest/raw/normalized/metric/report saving,
- artifact references with checksum and size metadata.
