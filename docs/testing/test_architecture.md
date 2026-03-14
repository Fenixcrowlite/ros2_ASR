# Test Architecture

## Principles
- Test architecture follows platform boundaries, not file-type convenience.
- Runtime, benchmark, gateway, GUI, config, storage, and CLI flows are validated at different layers.
- Cloud and ROS-heavy tests are isolated from the default fast suite.
- Browser E2E tests use the real web UI and a live FastAPI server, but deterministic fake backend state.

## Levels

### Unit
- Scope: pure domain logic.
- Targets: config merge logic, secret masking/resolution, dataset manifest parsing, metrics, normalized result model, artifact utilities.
- Tooling: `pytest`.

### Component
- Scope: one module as a black box without full system startup.
- Targets: `ProviderManager`, `BenchmarkOrchestrator`.
- Tooling: `pytest`, temp project roots, fake providers.

### Contract
- Scope: cross-package behavioral contracts that must remain stable.
- Targets: provider adapter contract, dataset manifest contract, normalized result contract, gateway response contract.
- Tooling: `pytest`, deterministic stubs/fakes.

### API
- Scope: gateway/backend HTTP behavior.
- Targets: runtime, benchmark, datasets, results, diagnostics, logs, secrets endpoints.
- Tooling: `fastapi.testclient.TestClient`.

### GUI
- Scope: frontend shell and asset serving.
- Targets: index page, static asset wiring, page skeleton availability.
- Tooling: `TestClient`.

### E2E
- Scope: realistic user flows through the live gateway and browser-rendered GUI.
- Targets: runtime happy path, benchmark-to-results flow, diagnostics visibility.
- Tooling: `uvicorn`, `requests`, `playwright`.

### Integration / CLI
- Scope: script-driven engineering workflows.
- Targets: config validation CLI, dataset import CLI, report export CLI.
- Tooling: `subprocess`.

### Regression
- Scope: stability of critical persisted outputs and schemas.
- Targets: benchmark artifact layout completeness.
- Tooling: `pytest`.

## Supporting Strategy
- Fake providers are used where deterministic outputs are required.
- A temporary project root is cloned for gateway/API/UI tests to avoid mutating repository state.
- Legacy tests remain available but are explicitly marked `legacy`.
