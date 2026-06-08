# Documentation Overview

This documentation is organized so that a new user can move from a clean Ubuntu machine to a running local ASR stack without reading the entire repository first.

## Recommended reading order

1. [Setup from a fresh Ubuntu machine](setup.md) — install tools, clone the repository, build the workspace, and start the first local Whisper run.
2. [ASR backend activation reference](asr_backends.md) — enable any included local or cloud backend and open its official upstream documentation.
3. [Provider environment setup](provider_env.md) — copy the safe local template and configure only the backends you plan to use.
4. [Provider-specific CLI checks](provider_cli.md) — optionally validate and test the backend you explicitly selected.
5. [Providers](providers.md) — inspect provider-specific setup details and runtime expectations.
6. [Runtime and ROS 2 nodes](runtime.md) — understand the difference between `make up` and `make up-runtime`, inspect the ROS 2 graph, and select another provider.
7. [Web UI](web_ui.md) — use the browser interface and gateway API.
8. [Configuration profiles](configuration.md) — understand YAML profiles and secret references.
9. [Datasets](datasets.md) — validate and import dataset manifests.
10. [Benchmarking](benchmarking.md) — optionally run benchmark suites and generate reports.
11. [Testing and maintenance](testing.md) — optionally run tests, documentation checks, lint checks, cleanup, and release checks.
12. [Architecture](architecture.md) — inspect the package structure and data flow after the basic setup works.
13. [Public repository release checklist](public_release_checklist.md) — verify visibility, clean-clone setup, secret safety, and demonstration backends before sharing the repository.

## First-run command sequence

After ROS 2 Jazzy has been installed, the normal local path is:

```bash
git clone https://github.com/Fenixcrowlite/ros2_ASR.git
cd ros2_ASR
make setup
make build
make up
```

Open:

```text
http://127.0.0.1:8088
```

Stop it with:

```bash
make down
```

Optional verification from another terminal:

```bash
cd ros2_ASR
make test-gateway-smoke
```

## Repository layout

- `ros2_ws/src/asr_interfaces` — ROS 2 messages, services, and actions.
- `ros2_ws/src/asr_core` — shared ASR models, language helpers, and audio helpers.
- `ros2_ws/src/asr_runtime_nodes` — live and replayed runtime pipeline.
- `ros2_ws/src/asr_provider_*` — local and cloud provider adapters.
- `ros2_ws/src/asr_benchmark_core` — benchmark execution without ROS UI code.
- `ros2_ws/src/asr_benchmark_nodes` — ROS action/service layer for benchmarks.
- `ros2_ws/src/asr_metrics` — quality, timing, resource, and summary metrics.
- `ros2_ws/src/asr_storage` — artifact path and persistence helpers.
- `ros2_ws/src/asr_reporting` — report/export helpers.
- `ros2_ws/src/asr_gateway` — FastAPI gateway for the web UI and automation.
- `web_ui` — static browser UI served by the gateway flow.
- `configs` — runtime, provider, benchmark, dataset, metric, GUI, and deployment profiles.
- `datasets` — registry files and small checked-in manifests.
- `secrets/refs` — checked-in non-secret credential reference definitions.
- `scripts` — setup, validation, benchmark, report, and maintenance helpers.
- `tests` — unit, contract, component, API, GUI, integration, and regression tests.

## Runtime model

The runtime path is split into small stages:

1. audio is read from a file or microphone;
2. audio is resampled, mixed to mono when needed, and normalized;
3. speech activity detection creates bounded speech segments;
4. the orchestrator calls the selected ASR provider adapter;
5. results, status, metrics, and artifacts are published or stored.

The browser UI uses `asr_gateway` as the single HTTP boundary. The frontend does not read ROS state, logs, provider settings, or artifact directories directly.
