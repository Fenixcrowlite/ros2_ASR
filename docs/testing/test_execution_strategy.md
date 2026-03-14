# Test Execution Strategy

## Fast Baseline
- Command:
  - `pytest -m "not cloud and not ros and not e2e and not slow and not legacy" -q`
- Intended for:
  - local development
  - CI on push / pull request
- Includes:
  - unit
  - component
  - contract
  - api
  - gui shell
  - integration CLI
  - regression

## Extended Local / Pre-Release
- Command:
  - `pytest -m "e2e or ros or cloud" -q`
- Intended for:
  - manual validation before demos
  - dedicated validation environments

## Legacy Coverage
- Command:
  - `pytest -m legacy -q`
- Purpose:
  - keep historical paths observable without blocking the new baseline

## CI Policy
- Primary CI job now excludes `legacy`, `e2e`, `slow`, `cloud`, and `ros`.
- Browser, ROS, and live-cloud suites should run in extended environments where dependencies and credentials are controlled.
