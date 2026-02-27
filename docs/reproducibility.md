# Reproducibility

## Environment

- Ubuntu 24.04 (Noble)
- ROS2 Jazzy
- Python 3.12

## Steps

```bash
make setup
make build
make test-unit
make test-ros
make test-colcon
make test
make bench
make report
```

## Determinism Controls

- Mock backend default for deterministic CI.
- Seeded noise generation in benchmark.
- Cloud tests gated with `pytest -m cloud` and credentials checks.
- No secrets in repository.
