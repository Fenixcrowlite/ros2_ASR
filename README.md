# Universal ASR for ROS2 Jazzy

Production-oriented modular ASR integration for ROS2 (Ubuntu 24.04, Jazzy, Python) with local and commercial backends, benchmark tooling, metrics, and reproducible experiments.

## Features

- Unified ASR core API across providers.
- ROS2 interfaces (`msg/srv/action`) for one-shot and long-running transcription.
- Backends:
  - Local: `mock`, `vosk`, `whisper`.
  - Cloud: `google`, `aws`, `azure`.
- Runtime backend switch through ROS2 service and config.
- Benchmark scenarios (clean/noisy, language variants, streaming simulation).
- Metrics: WER, CER, latency breakdown, RTF, CPU/RAM/GPU, error rate, cost estimate.
- Reproducible scripts and report generation.

## Repository Layout

- `docs/` architecture, interfaces, benchmark methodology, reproducibility, cloud setup.
- `docs/newbie_guide.md` plain-language "how it works" map for first-time readers.
- `configs/` YAML configs and cloud example config.
- `data/sample` sample WAV files and transcripts.
- `ros2_ws/src/` ROS2 packages.
- `scripts/` setup, run, benchmark, plotting, report.
- `results/` benchmark outputs.

## Quick Start

```bash
make setup
make build
make test-unit
make test-ros
make test-colcon
make test
make run
make bench
make report
bash scripts/release_check.sh
```

`make bench` runs the benchmark runner and generates `results/*.csv`, `results/*.json`,
and `results/plots/*.png` in a single pass (no duplicate plotting step).

## Release Build

Create a sterile archive for submission:

```bash
make dist
```

The archive is generated in `dist/`:

- `dist/ros2_asr_release_YYYYMMDD_HHMMSS.tar.gz`

Included in release package:

- `ros2_ws/src/**` sources
- `docs/`
- `configs/` (example configs, no private commercial config)
- `scripts/`
- `data/sample/` and `data/transcripts/`
- `results/` (benchmark CSV/JSON/plots)
- root files: `README.md`, `Makefile`, `pyproject.toml`, `requirements.txt`

Excluded from release package:

- build artifacts: `build/`, `install/`, `log/`
- caches and bytecode: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- environments and VCS: `.venv*/`, `.git/`
- secrets: `configs/commercial.yaml`, `.env`, key/cert files

## ROS2 Demo

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch asr_ros demo.launch.py
```

In another terminal:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 service call /asr/recognize_once asr_interfaces/srv/RecognizeOnce "{wav_path: data/sample/en_hello.wav, language: en-US, enable_word_timestamps: true}"
```

## Live Microphone Recognition

Run demo with microphone input and live chunk processing:

```bash
source .venv/bin/activate
export PYTHONPATH="$(python -c 'import site; print(site.getsitepackages()[0])'):${PYTHONPATH}"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch asr_ros bringup.launch.py config:=configs/live_mic_whisper.yaml input_mode:=mic
```

Where to view recognized text:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /asr/text --qos-durability transient_local
```

If your DDS reports QoS incompatibility, use:

```bash
ros2 topic echo /asr/text --once --qos-durability transient_local --qos-reliability reliable
```

Optional telemetry view:

```bash
ros2 topic echo /asr/metrics
```

Notes:
- `input_mode:=mic` records from microphone; if microphone is unavailable, `audio_capture_node` falls back to file mode.
- Microphone mode is continuous by default; new recognition results are published repeatedly while you speak.
- For deterministic/local smoke checks without ML models, switch to mock backend:
  `ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: mock, model: '', region: ''}"`.

## Cloud Credentials

Do not commit secrets. Use environment variables and local-only `configs/commercial.yaml` copied from `configs/commercial.example.yaml`.

See `docs/commercial_setup.md`.
