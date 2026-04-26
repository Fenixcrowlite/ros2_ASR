# Test Execution Strategy

## Primary Validation

- `make test-unit`
- `make test-ros`
- `make test-colcon`

## Scope

- Primary suites cover the canonical packages in `ros2_ws/src` plus gateway/UI and top-level scripts still used in production flows.
- Archived assets under `legacy/` are intentionally excluded from the default test matrix.

## Benchmark/Report Checks

- `make bench`
- `make report`
