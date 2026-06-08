# Setup from a Fresh Ubuntu 24.04 Machine

This guide explains the shortest reliable path from a clean Ubuntu 24.04 installation to a working local ASR stack. The first successful run uses local Whisper and does not require cloud credentials.

## 1. Install ROS 2 Jazzy

Install ROS 2 Jazzy using the official Ubuntu package instructions:

```text
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
```

Confirm that the ROS environment exists:

```bash
test -f /opt/ros/jazzy/setup.bash && echo "ROS 2 Jazzy found"
```

Expected output:

```text
ROS 2 Jazzy found
```

If the file is missing, finish the ROS 2 installation before continuing.

## 2. Install system tools

```bash
sudo apt update
sudo apt install -y \
  git \
  make \
  python3-venv \
  python3-pip \
  python3-colcon-common-extensions \
  build-essential \
  lsof \
  curl \
  unzip
```

`python3-colcon-common-extensions` provides the `colcon` command used by `make build`. `unzip` is required only when `make setup-vosk` is used.

Confirm that `colcon` is available:

```bash
command -v colcon >/dev/null && echo "colcon found"
```

## 3. Clone the public repository

```bash
git clone https://github.com/Fenixcrowlite/ros2_ASR.git
cd ros2_ASR
```

## 4. Create the Python environment

```bash
make setup
```

This command creates `.venv/`, installs dependencies from `requirements.txt`, installs the local `archviz` wrapper, and prints the next steps.

Activate the environment only when running project scripts manually:

```bash
source .venv/bin/activate
```

The `make` targets activate it automatically where needed.

## 5. Build the ROS 2 workspace

```bash
make build
```

Generated files are written under:

```text
ros2_ws/build
ros2_ws/install
ros2_ws/log
```

These directories are local outputs and are ignored by Git.

## 6. Start the full local application

```bash
make up
```

Open:

```text
http://127.0.0.1:8088
```

Keep the terminal open while the stack is running.

The default provider is:

```text
providers/whisper_local
```

The default preset is CPU-safe. The first transcription can take longer because the Whisper model may be downloaded and cached locally.

## 7. Stop the application

```bash
make down
```

## Optional verification

The application can be started without running tests. Use the checks below when you want to verify the setup, diagnose a problem, or prepare the repository for sharing.

Verify the running browser UI, gateway endpoints, and one bundled local Whisper transcription:

```bash
make test-gateway-smoke
```

Check documentation consistency and sample dataset metadata:

```bash
make docs-check
make validate-datasets
```

Run Python and ROS-related tests:

```bash
make test-unit
make test-ros
make test-colcon
```

Before publishing or sharing the repository, run:

```bash
make public-release-check
```

The ROS tests require ROS 2 Jazzy. Optional provider checks may require downloaded models or cloud credentials.

## Minimal ROS 2 runtime without the browser UI

```bash
make up-runtime
```

This command runs in the foreground. Stop it with `Ctrl+C`.

Inspect the active ROS 2 graph from another terminal:

```bash
cd ros2_ASR
make rqt
```

## Configure another provider

The default local Whisper path needs no external account.

For commands that enable every supported backend, read:

```text
docs/asr_backends.md
```

For cloud and hosted providers, create the local environment file safely:

```bash
make init-provider-env
nano secrets/local/runtime.env
```

The initializer copies the tracked empty template only when the local file does not exist, applies file mode `600`, and keeps an existing configuration unchanged.

Detailed explanations are in:

```text
docs/provider_env.md
docs/provider_cli.md
docs/providers.md
```

## Optional Vosk setup

Vosk is not needed for the first Whisper-based run. Download the optional models and bundled sample WAV with:

```bash
make setup-vosk
```

Then start Vosk:

```bash
make up PROVIDER_PROFILE=providers/vosk_local
```

## Run the default benchmark

Benchmarking is optional and is not required to start the application.

```bash
make bench-suite
make report
```

## Clean local outputs

```bash
make clean
```

To recreate the Python environment:

```bash
rm -rf .venv
make setup
```

## Troubleshooting

### `ROS2 Jazzy not found at /opt/ros/jazzy/setup.bash`

```bash
ls -l /opt/ros/jazzy/setup.bash
```

Install ROS 2 Jazzy or use the supported Ubuntu 24.04 host.

### `colcon: command not found`

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions
command -v colcon
```

### `.venv missing. Run make setup first.`

```bash
make setup
```

### Port `8088` is already in use

```bash
make down
make up GATEWAY_PORT=8090
```

Then open:

```text
http://127.0.0.1:8090
```

### First Whisper transcription takes a long time

The selected model may be downloading on first use. Keep the terminal open. Later runs reuse the cached model.

### Vosk reports missing models

```bash
make setup-vosk
```

### Cloud provider validation fails

Check `secrets/local/runtime.env`, read `docs/provider_env.md`, and confirm that the required provider-side API or resource has been enabled. Missing cloud configuration must not affect the default local Whisper run.
