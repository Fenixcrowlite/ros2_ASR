# Universal ASR for ROS2 Jazzy

Production-oriented modular ASR integration for ROS2 (Ubuntu 24.04, Jazzy, Python) with local and commercial backends, benchmark tooling, metrics, and reproducible experiments.

## Architecture Baseline

The repository now includes a modular ROS2-first baseline with explicit runtime/benchmark split and gateway boundary.

- Runtime packages: `asr_runtime_nodes`, `asr_provider_base`, `asr_provider_*`, `asr_config`, `asr_storage`.
- Benchmark packages: `asr_datasets`, `asr_benchmark_core`, `asr_benchmark_nodes`, `asr_metrics`, `asr_reporting`.
- Gateway/UI: `asr_gateway`, `web_ui`.
- Launch package: `asr_launch`.
- Extended interface contract: `asr_interfaces`.

Primary architecture docs:
- `docs/architecture/system_overview.md`
- `docs/architecture/runtime_architecture.md`
- `docs/architecture/benchmark_architecture.md`
- `docs/architecture/implementation_report.md`

## Features

- Unified ASR core API across providers.
- ROS2 interfaces (`msg/srv/action`) for one-shot and long-running transcription.
- Backends:
  - Local: `mock`, `vosk`, `whisper`.
  - Cloud: `google`, `aws`, `azure`.
- Runtime backend switch through ROS2 service and config.
- Benchmark scenarios (clean/noisy, language variants, streaming simulation).
- Metrics: corpus-level WER/CER in summaries, exact-match sample accuracy, latency/RTF, success-failure rate, CPU/RAM/GPU, and cost estimate.
- Reproducible scripts and report generation.

## Repository Layout

- `docs/` architecture, interfaces, benchmark methodology, reproducibility, cloud setup.
- `docs/newbie_guide.md` plain-language "how it works" map for first-time readers.
- `docs/run_guide.md` step-by-step launch/runbook (live mic, topics, tests, troubleshooting).
- `docs/wiki/` Obsidian-ready wiki network (modular pages + cross-links).
- `configs/` YAML configs and cloud example config.
- `configs/runtime|providers|benchmark|datasets|metrics|deployment|gui` profile sets.
- `secrets/refs/` secret references (no inline credentials in provider profiles).
- `artifacts/` runtime session and benchmark run outputs.
- `datasets/` registry/raw/imported/manifests/processed/noise assets.
- `web_ui/` new gateway-first UI skeleton.
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
make web-gui-lan
make arch
bash scripts/release_check.sh
```

`make bench` runs the benchmark runner and generates `results/*.csv`, `results/*.json`,
and `results/plots/*.png` in a single pass (no duplicate plotting step).

For the newer gateway/core benchmark path, the canonical per-run artifacts live under
`artifacts/benchmark_runs/<run_id>/...`. Those summaries expose grouped metric sections
(`provider_summaries`, `quality_metrics`, `latency_metrics`, `reliability_metrics`,
`cost_metrics`, `streaming_metrics`) plus `metric_statistics`/`metric_metadata`.
For multi-provider runs, `provider_summaries` is the only metric analysis surface and
the mixed top-level metric aggregate is intentionally left empty. `WER`/`CER` inside
provider summaries are corpus-level aggregates, `sample_accuracy` is exact normalized
match rate, and `metric_statistics.estimated_cost_usd.sum` is the total estimated run cost.

Optional external-corpus smoke suite:

```bash
bash scripts/download_dataset_optional.sh
python scripts/run_external_dataset_suite.py --mode core
python scripts/run_external_dataset_suite.py --mode both --api-base-url http://127.0.0.1:8088
```

That path now rebuilds `12` tiny reproducible subsets from large public corpora
and verifies both the direct benchmark core path and the live gateway benchmark
path. The latest combined suite summary is stored in
`results/external_dataset_suite_20260326T182557Z.md`, and the system-level
assessment is summarized in `SYSTEM_QUALITY_ASSESSMENT.md`.

Dataset manifests may keep relative `audio_path` values. They are resolved relative
to the manifest file location, not the caller `cwd`. Uploaded manifest bundles are
also rejected if filenames collide after basename normalization or if the manifest
references audio files that were not uploaded with the bundle.

Managed `asr_launch` stacks are single-instance per workspace by design. If another runtime/gateway/benchmark stack from this repository is still alive, a new launch fails fast with the conflicting PIDs instead of mixing ROS topics, services, and logs.

In the browser UI:

- `Start Live Runtime` runs the full live ROS pipeline.
- In file-mode the selected WAV is replayed as a paced stream, so the Runtime page shows segment-level results.
- `Transcribe Whole File` uses the direct one-shot path for one transcript of the entire WAV.

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

Docsbot LLM behavior is explicit:

- default `DOCSBOT_LLM_PROVIDER=auto`: use OpenAI only when `OPENAI_API_KEY` exists
- without a key in `auto`: generate template-only pages, no synthetic mock drafts
- `DOCSBOT_LLM_PROVIDER=openai`: fail fast if the key is missing
- `DOCSBOT_LLM_PROVIDER=mock`: opt in to deterministic mock drafts explicitly

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

`make arch-runtime` and `make arch` now fail fast if another managed stack from
the same workspace is already running. Stop `make web-gui`, `full_stack_dev`,
or other managed launches first, otherwise runtime graph extraction would be
polluted by unrelated live nodes/topics/services.

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
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch asr_launch runtime_minimal.launch.py \
  runtime_profile:=default_runtime \
  provider_profile:=providers/whisper_local
```

In another terminal:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 service call /asr/runtime/recognize_once asr_interfaces/srv/RecognizeOnce \
  "{wav_path: data/sample/vosk_test.wav, language: en-US, enable_word_timestamps: true, session_id: '', provider_profile: '', provider_preset: '', provider_settings_json: '{}'}"
```

`make run` is a thin wrapper around this launch path.

## Live Runtime Session

Fastest live smoke path:

```bash
./scripts/open_live_test_terminals.sh
```

The helper now starts the current `asr_launch/runtime_streaming.launch.py` stack,
waits for `/asr/runtime/start_session`, starts the session, and subscribes to
the structured final-result topic.

Manual live run:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch asr_launch runtime_streaming.launch.py \
  runtime_profile:=default_runtime \
  provider_profile:=providers/whisper_local \
  input_mode:=mic
```

In another terminal, start the runtime session:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 service call /asr/runtime/start_session asr_interfaces/srv/StartRuntimeSession \
  "{runtime_profile: default_runtime, provider_profile: providers/whisper_local, provider_preset: '', provider_settings_json: '{}', session_id: '', runtime_namespace: /asr/runtime, auto_start_audio: true, processing_mode: segmented, audio_source: mic, audio_file_path: data/sample/vosk_test.wav, language: en-US, mic_capture_sec: 6.0}"
```

Watch final ASR results:

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 topic echo /asr/runtime/results/final --qos-durability transient_local --qos-reliability reliable
```

Open `rqt` against the correct workspace overlay:

```bash
bash scripts/run_rqt.sh
```

Notes:
- There is no primary `/asr/text/plain` topic in the new runtime stack; the supported result feed is `/asr/runtime/results/final`.
- Runtime launch alone does not auto-capture audio. Live flow begins after `/asr/runtime/start_session`.
- The orchestrator logs every final runtime result to the launch terminal, so manual runs are no longer silent without a separate subscriber.
- `/asr/runtime/results/final` is retained with `transient_local`; for late CLI inspection use `ros2 topic echo /asr/runtime/results/final --qos-durability transient_local --qos-reliability reliable`.
- `audio_source=mic` uses the microphone; `audio_source=file` replays a WAV through the same runtime pipeline.
- Runtime control/status services are now `/asr/runtime/*`, not legacy `/asr/set_backend` and `/asr/get_status`.
- Do not launch `rqt` from a desktop shortcut or a shell that only sourced a stale top-level `install/setup.bash`; use `ros2_ws/install/setup.bash` or `scripts/run_rqt.sh` so `asr_interfaces/*` types are importable.

## Legacy Compatibility Sample Evaluation

`scripts/run_live_sample_eval.sh` is kept for compatibility checks across the old
`core`, `ros_service`, and `ros_action` paths. It still exercises the legacy
`asr_ros` service/action surface and should not be treated as the primary
operator runbook for the modular runtime stack.

It records one microphone sample and runs it through selected interfaces/backends
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

Compatibility-tool guardrails:

- `--language-mode auto` now fails fast if `faster-whisper` language detection is unavailable; it no longer falls back silently to config language.
- `--interfaces ros_action --action-streaming` is valid only for streaming-capable backends. Batch-only targets such as Whisper are rejected before any run starts.

## Web GUI Control Center (New Gateway-First UI)

Run full browser control center (runtime + benchmark + diagnostics) via the new `web_ui` + `asr_gateway` stack:

```bash
make web-gui
```

`make web-gui` now launches:
- ROS2 runtime nodes,
- benchmark manager node,
- `asr_gateway` backend serving new `web_ui` at `http://localhost:8088`.

If you need to stop an already running stack cleanly before relaunching:

```bash
bash scripts/run_web_ui.sh --stop --port 8088
```

For LAN access:

```bash
make web-gui-lan
```

Then open:

```text
http://localhost:8088
```

New GUI docs:
- `docs/gui/README.md`
- `web_ui/README.md`

## Cloud Credentials

Do not commit secrets. Use environment variables and local-only `configs/commercial.yaml` copied from `configs/commercial.example.yaml`.

Gateway/runtime cloud runs are fail-fast by design:
- `google` validates service-account file setup before provider use.
- `azure` validates key+region pairing before provider use.
- `aws` validates auth/profile metadata through secret refs before provider use.

The `web_ui` secrets page also supports:
- AWS SSO login status and refresh,
- Google service-account upload/clear,
- Azure env save/clear,
- environment preflight and runtime sample/noise tooling via the gateway.

See `docs/commercial_setup.md`.
