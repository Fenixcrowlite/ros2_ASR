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
- `docs/run_guide.md` step-by-step launch/runbook (live mic, topics, tests, troubleshooting).
- `docs/wiki/` Obsidian-ready wiki network (modular pages + cross-links).
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
make live-sample
make bench
make report
make web-gui
make arch
bash scripts/release_check.sh
```

`make bench` runs the benchmark runner and generates `results/*.csv`, `results/*.json`,
and `results/plots/*.png` in a single pass (no duplicate plotting step).

## Obsidian Wiki

Project wiki vault is available in `docs/wiki`.

Open `docs/wiki` as an Obsidian vault and start from:

- `docs/wiki/00_Start/Wiki_Home.md`

## Docsbot (Auto Obsidian Wiki)

Autonomous wiki generator/updater is available in `tools/docsbot`.
It auto-detects repo root and Obsidian vault (priority includes `~/Desktop`), then writes all generated content into one vault subfolder `Wiki-ASR`.

Quick commands:

```bash
make docsbot-detect
make docsbot-snapshot
make docsbot-generate
make docsbot-validate
make docsbot-watch
make docsbot-install-hooks
```

Direct CLI (from tool venv):

```bash
tools/docsbot/.venv/bin/docsbot detect
tools/docsbot/.venv/bin/docsbot generate
tools/docsbot/.venv/bin/docsbot validate
tools/docsbot/.venv/bin/docsbot watch
```

Generated structure in vault subfolder:

- `00_Home.md`
- `01_Project/Overview.md`, `01_Project/Glossary.md`
- `02_Architecture/Layered Architecture.md`, `Dataflow.md`, `ROS Graph.md`, `Module Map.md`
- `03_API/{Services,Topics,Messages,Parameters}/...`
- `04_Modules/<module>/<module>.md`
- `90_Auto/_Index.md`, `_Changelog.md`, `_Errors.md`, `_Generated Graph.md`

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

## Architecture Diagrams

Architecture diagrams are generated automatically from:

- static source analysis (`package.xml`, `setup.py`, launch files, Python AST),
- runtime ROS2 inspection (`ros2 node/topic/service` commands),
- anti-gap merge policy (everything from static is always retained, missing runtime evidence is marked `expected_only`).

Run pipeline:

```bash
make build
make arch-static
make arch-runtime
make arch
make arch-diff
```

Direct CLI:

```bash
source .venv/bin/activate
archviz static --ws ros2_ws --out docs/arch
archviz runtime --ws ros2_ws --out docs/arch --profile full --timeout-sec 20
archviz merge --static docs/arch/static_graph.json --runtime docs/arch/runtime_graph.json --out docs/arch/merged_graph.json
archviz render --in docs/arch/merged_graph.json --out docs/arch --format mermaid
archviz diff --a docs/arch/merged_graph_prev.json --b docs/arch/merged_graph.json --out docs/arch/CHANGELOG_ARCH.md
archviz all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20
```

Generated artifacts in `docs/arch/`:

- `static_graph.json`, `runtime_graph.json`, `merged_graph.json`
- `mindmap.mmd`, `flow.mmd`, `seq_recognize_once.mmd`
- `CHANGELOG_ARCH.md`, `runtime_errors.md`

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
ros2 topic echo /asr/text/plain --qos-durability transient_local
```

If your DDS reports QoS incompatibility, use:

```bash
ros2 topic echo /asr/text/plain --once --qos-durability transient_local --qos-reliability reliable
```

Optional telemetry view:

```bash
ros2 topic echo /asr/metrics
```

Notes:
- `asr_text_output_node` is started in bringup by default and republishes plain text to `/asr/text/plain`.
- Structured result message remains available on `/asr/text`.
- `input_mode:=mic` records from microphone; if microphone is unavailable, `audio_capture_node` falls back to file mode.
- Microphone mode is continuous by default; new recognition results are published repeatedly while you speak.
- For deterministic/local smoke checks without ML models, switch to mock backend:
  `ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: mock, model: '', region: ''}"`.

## Live Sample Evaluation (Record + Compare Interfaces)

Record one microphone sample and run it through selected interfaces/backends
with metrics collection:

Interactive mode (record first, then choose language mode and model runs):

```bash
bash scripts/run_live_sample_eval.sh
```

Direct non-interactive example:

```bash
bash scripts/run_live_sample_eval.sh \
  --interfaces core,ros_service,ros_action \
  --model-runs whisper:tiny,whisper:large-v3,mock \
  --language-mode auto \
  --ros-auto-launch \
  --reference-text "hello world"
```

Artifacts are written to `results/live_sample/<timestamp>/`:

- recorded wav (`live_sample.wav`)
- `live_results.json`
- `live_results.csv`
- `summary.md`
- `plots/*.png`

Useful options:

- `--interfaces core,ros_service,ros_action`
- `--backends mock,vosk,whisper,google,aws,azure`
- `--model-runs whisper:tiny,whisper:large-v3,mock`
- `--record-sec 5.0`
- `--language-mode manual|auto|config`
- `--language en-US`
- `--use-wav /path/to/existing.wav`
- `--action-streaming`

## Web GUI Control Center

Run full browser control center (configs/models/languages/secrets/upload/noise/live/benchmark/ROS bringup):

```bash
make web-gui
```

Then open:

```text
http://localhost:8765
```

Module docs:

- `web_gui/README.md`

## Cloud Credentials

Do not commit secrets. Use environment variables and local-only `configs/commercial.yaml` copied from `configs/commercial.example.yaml`.

See `docs/commercial_setup.md`.
