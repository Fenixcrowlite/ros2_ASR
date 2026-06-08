# Architecture

The project is organized around one shared ASR contract and three execution
surfaces: runtime, benchmark, and gateway.

## Layers

- Interfaces: `asr_interfaces` defines ROS 2 messages, services, and actions.
- Core: `asr_core` defines shared models, audio helpers, language helpers, and
  normalized result structures.
- Providers: `asr_provider_base` defines the adapter contract and provider
  registry; `asr_provider_*` packages implement concrete providers.
- Runtime: `asr_runtime_nodes` runs live or replayed audio through the ASR
  pipeline.
- Benchmark: `asr_benchmark_core` executes provider/dataset scenarios and
  computes result payloads; `asr_benchmark_nodes` exposes benchmark execution
  through ROS.
- Metrics and storage: `asr_metrics`, `asr_storage`, and `asr_reporting`
  compute metrics and write outputs.
- Gateway and UI: `asr_gateway` exposes HTTP endpoints; `web_ui` renders the
  browser interface.

## Runtime Path

```text
audio input -> preprocessing -> VAD segmentation -> provider call -> ASR result
```

The orchestrator owns provider selection and runtime services. Provider
adapters return normalized results so downstream metrics and UI code do not
depend on provider-specific payloads.

## Benchmark Path

```text
dataset registry -> benchmark profile -> provider adapters -> metrics -> artifacts
```

The benchmark core can be run from scripts, make targets, or ROS-facing
benchmark nodes. The same provider profiles are used by runtime and benchmark
flows.

## Gateway Path

```text
browser UI -> FastAPI gateway -> ROS services/actions and local helpers
```

The gateway is the stable boundary for frontend and automation clients. It
validates payloads, projects profiles into browser-friendly JSON, starts
runtime and benchmark work, and reads result summaries.

## Generated Architecture Outputs

The `archviz` helper can inspect the workspace and write diagrams or graph JSON
under `artifacts/archviz`:

```bash
make arch-static
make arch-runtime
make arch
make arch-diff
```

These outputs are local artifacts and are not tracked.
