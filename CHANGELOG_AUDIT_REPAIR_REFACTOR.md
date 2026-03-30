# Changelog Audit Repair Refactor

## 2026-03-30

### Repaired

- Added `scripts/run_benchmark_core.py` as canonical benchmark CLI wrapper.
- Switched `scripts/run_benchmarks.sh` to canonical benchmark core.
- Switched `make report` to canonical benchmark summary input.
- Extended `scripts/generate_report.py` to support canonical summary JSON.
- Reworked gateway log collection to preserve component/source metadata and global ordering.
- Reworked logs page UI to render structured log entries instead of raw text dump.

### Clarified

- Marked `asr_benchmark` runner/node as legacy compatibility.
- Updated GUI backend contract for structured `/api/logs` payload.

### Verified

- targeted CLI/report/log API tests passed
- targeted e2e logs-flow test was skipped by environment, not failed
