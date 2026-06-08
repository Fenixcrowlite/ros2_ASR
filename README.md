# ROS 2 ASR Integration Prototype

This repository contains a ROS 2 prototype for integrating and evaluating automatic speech recognition (ASR) in robotic applications. It targets Ubuntu 24.04 and ROS 2 Jazzy. The project supports local providers such as Whisper and Vosk, optional cloud providers, a ROS 2 runtime pipeline, benchmark tools, and a local browser UI.

## Start here

For a fresh Ubuntu machine, follow the complete [setup guide](docs/setup.md). After ROS 2 Jazzy has been installed, the shortest path to a running local application is:

```bash
test -f /opt/ros/jazzy/setup.bash && echo "ROS 2 Jazzy found"
command -v colcon >/dev/null && echo "colcon found"
```

If `colcon` is missing, install it before building:

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions
```

Clone, prepare, build, and start the project:

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

Stop the managed stack:

```bash
make down
```

The default provider is local Whisper. Cloud credentials are not required for this first run. The first transcription can take longer because the selected Whisper model may be downloaded and cached locally.

## Optional verification

The application can be started without running the test suite. Use these checks when you want to verify the setup, diagnose a problem, or prepare the repository for sharing.

Verify the running UI, gateway endpoints, and one bundled local transcription:

```bash
make test-gateway-smoke
```

Check documentation consistency and sample dataset metadata:

```bash
make docs-check
make validate-datasets
```

Run the static public-release audit before sharing the repository:

```bash
make public-release-check
```

## Supported environment

- Ubuntu 24.04
- ROS 2 Jazzy installed at `/opt/ros/jazzy/setup.bash`
- Python 3.12
- `colcon` available in `PATH`
- optional NVIDIA GPU for faster local Whisper execution
- internet connection and credentials only when cloud providers are used

## What the project contains

- `ros2_ws/src/asr_runtime_nodes` — audio input, preprocessing, VAD segmentation, and ASR orchestration nodes;
- `ros2_ws/src/asr_provider_*` — provider adapters for local and cloud ASR solutions;
- `ros2_ws/src/asr_benchmark_*` — benchmark execution and ROS 2 benchmark interfaces;
- `ros2_ws/src/asr_interfaces` — shared ROS 2 messages, services, and actions;
- `ros2_ws/src/asr_metrics`, `asr_reporting`, `asr_storage` — metric calculation, summaries, and result storage;
- `ros2_ws/src/asr_gateway`, `web_ui` — optional backend and local browser interface;
- `configs`, `datasets`, `scripts`, `tests` — configuration, sample manifests, utility scripts, and automated checks.

## Common commands

### Normal use

```bash
make setup                # create .venv and install Python dependencies
make build                # build the ROS 2 workspace
make up                   # start the full local stack with the browser UI
make up-runtime           # start only the minimal ROS 2 runtime in the foreground
make down                 # stop the managed browser UI stack
make public-help          # show public setup and provider commands
make init-provider-env    # create secrets/local/runtime.env safely from the empty template
make setup-vosk           # download the optional Vosk models and sample WAV
make rqt                  # open rqt with the project workspace environment
```

### Optional checks and maintenance

```bash
make test-gateway-smoke   # verify UI/API routes and one local Whisper transcription
make provider-validate    # validate the selected ASR backend through the running gateway
make provider-test        # run a real WAV transcription with the selected ASR backend
make docs-check           # verify public setup guides and provider documentation
make validate-datasets    # validate checked-in dataset metadata
make test-unit            # run fast Python tests
make test-ros             # run ROS integration tests
make test-colcon          # run ROS package tests
make public-release-check # run static checks before sharing the repository
make bench-suite          # run the default benchmark suite
make report               # generate a report from the latest benchmark run
```

The public convenience targets are layered through `GNUmakefile` and `mk/public_tools.mk`. The established project `Makefile` remains intact.

## Local runtime without the browser UI

```bash
make up-runtime
```

This command runs in the foreground. Stop it with `Ctrl+C`. In another terminal, use `make rqt` when you want to inspect the active ROS 2 graph.

## Optional providers

The first run uses `providers/whisper_local`. Other provider profiles can be selected explicitly:

```bash
make up PROVIDER_PROFILE=providers/vosk_local
make up PROVIDER_PROFILE=providers/azure_cloud
make up PROVIDER_PROFILE=providers/google_cloud
make up PROVIDER_PROFILE=providers/aws_cloud
```

Vosk requires local model folders. Prepare them with:

```bash
make setup-vosk
```

Cloud providers require credentials and may create provider-side usage costs. Create the ignored local environment file safely:

```bash
make init-provider-env
nano secrets/local/runtime.env
```

Do not commit real credentials.

For every supported backend, read the [ASR backend activation reference](docs/asr_backends.md). For local account-specific values, follow [Provider environment setup](docs/provider_env.md). For terminal validation of the selected backend, read [Provider-specific CLI checks](docs/provider_cli.md). For provider-specific expectations, read [Providers](docs/providers.md).

## Documentation

Read the pages in this order when setting up the project for the first time:

1. [Setup from a fresh Ubuntu machine](docs/setup.md)
2. [ASR backend activation reference](docs/asr_backends.md)
3. [Provider environment setup](docs/provider_env.md)
4. [Provider-specific CLI checks](docs/provider_cli.md)
5. [Providers](docs/providers.md)
6. [Runtime and ROS 2 nodes](docs/runtime.md)
7. [Web UI](docs/web_ui.md)
8. [Configuration profiles](docs/configuration.md)
9. [Datasets](docs/datasets.md)
10. [Benchmarking](docs/benchmarking.md)
11. [Testing and maintenance](docs/testing.md)
12. [Architecture](docs/architecture.md)
13. [Public repository release checklist](docs/public_release_checklist.md)

## Scope

The repository provides an integration prototype and benchmark utilities for selected ASR providers. It is not intended as a generic production platform. Safe mapping of recognized text to concrete robotic actions is outside the scope of this repository and must be implemented as a separate application layer.
