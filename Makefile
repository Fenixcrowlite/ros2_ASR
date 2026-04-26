SHELL := /bin/bash
.DEFAULT_GOAL := help
VENV := .venv
PY := $(VENV)/bin/python
ROS_SETUP := /opt/ros/jazzy/setup.bash
RUNTIME_PROFILE ?= default_runtime
PROVIDER_PROFILE ?= providers/whisper_local
BENCHMARK_PROFILE ?= default_benchmark
GATEWAY_MODE ?= local
GATEWAY_STACK ?= full
GATEWAY_PORT ?= 8088
LIVE_SAMPLE_ARGS ?=
RQT_ARGS ?=
HF_LOCAL_RUNTIME_PROFILE ?= huggingface_local_runtime
HF_API_RUNTIME_PROFILE ?= huggingface_api_runtime
HF_SMOKE_ARGS ?=
SRC_PY_PATH := $(shell find $(CURDIR)/ros2_ws/src -mindepth 1 -maxdepth 1 -type d | tr '\n' ':')
PY_PATH := $(CURDIR):$(SRC_PY_PATH)
ARCHVIZ := ./archviz
COLCON_CMAKE_PY_ARGS := --cmake-args -DPYTHON_EXECUTABLE=$(CURDIR)/$(VENV)/bin/python -DPython3_EXECUTABLE=$(CURDIR)/$(VENV)/bin/python
COLCON_EXTENSION_BLOCKLIST ?= colcon_core.event_handler.desktop_notification
COLCON_GLOBAL_ARGS := --log-base ros2_ws/log
COLCON_WS_ARGS := --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install
COLCON_TEST_WS_ARGS := --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install
LINT_RUFF_PATHS := \
	ros2_ws/src/asr_runtime_nodes \
	ros2_ws/src/asr_benchmark_core \
	ros2_ws/src/asr_datasets \
	ros2_ws/src/asr_metrics \
	ros2_ws/src/asr_provider_aws \
	ros2_ws/src/asr_provider_azure \
	ros2_ws/src/asr_provider_google \
	ros2_ws/src/asr_provider_whisper \
	ros2_ws/src/asr_provider_base
LINT_MYPY_PATHS := $(LINT_RUFF_PATHS)

.PHONY: help setup setup-vosk build test test-unit test-ros test-colcon run bench report web-gui web-gui-lan web-gui-stop up up-runtime up-lan down hf-smoke-local hf-smoke-api bench-hf rqt arch-static arch-runtime arch arch-diff lint lint-ruff lint-mypy security-scan format clean dist docsbot-setup docsbot-detect docsbot-snapshot docsbot-generate docsbot-validate docsbot-watch docsbot-install-hooks

help:
	@printf '%s\n' \
		'Main entrypoints:' \
		'  make up                Build and start the full web UI stack on localhost:8088' \
		'  make up-lan            Build and start the full web UI stack on 0.0.0.0:8088' \
		'  make up-runtime        Build and start the minimal ROS2 runtime stack' \
		'  make down              Stop the managed web UI stack on $$GATEWAY_PORT (default 8088)' \
		'  make hf-smoke-local    Run direct Hugging Face local provider smoke test' \
		'  make hf-smoke-api      Run direct Hugging Face API provider smoke test' \
		'  make bench-hf          Run the Hugging Face provider benchmark matrix' \
		'  make rqt               Launch rqt with this workspace environment' \
		'' \
		'Common variables:' \
		'  GATEWAY_MODE=local|lan GATEWAY_STACK=full|runtime GATEWAY_PORT=8088' \
		'  RUNTIME_PROFILE=default_runtime PROVIDER_PROFILE=providers/whisper_local' \
		'  HF_LOCAL_RUNTIME_PROFILE=huggingface_local_runtime HF_API_RUNTIME_PROFILE=huggingface_api_runtime' \
		'  HF_SMOKE_ARGS="--reference-text \"hello world\""'

setup:
	bash scripts/setup_env.sh

setup-vosk:
	bash scripts/maintenance/setup_vosk_models.sh

build:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP).'; exit 1; fi; if [ ! -f $(VENV)/bin/activate ]; then echo '.venv missing. Run make setup first.'; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_PYTHON_EXECUTABLE='$(CURDIR)/$(VENV)/bin/python' COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon $(COLCON_GLOBAL_ARGS) build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS)"

test-unit:
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) -m pytest -q -m "not (ros or legacy)"'

test-ros:
	bash -lc 'if [ ! -f $(ROS_SETUP) ]; then echo "ROS2 Jazzy not found at $(ROS_SETUP), skipping ROS tests."; exit 0; fi; if [ ! -f $(VENV)/bin/activate ]; then echo ".venv missing. Run make setup first."; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_PYTHON_EXECUTABLE="$(CURDIR)/$(VENV)/bin/python" COLCON_EXTENSION_BLOCKLIST="$(COLCON_EXTENSION_BLOCKLIST)" bash scripts/with_colcon_lock.sh colcon $(COLCON_GLOBAL_ARGS) build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS) && source ros2_ws/install/setup.bash && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) -m pytest -q -m "ros and not legacy" tests/integration'

test-colcon:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP), skipping colcon tests.'; exit 0; fi; if [ ! -f $(VENV)/bin/activate ]; then echo '.venv missing. Run make setup first.'; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_PYTHON_EXECUTABLE='$(CURDIR)/$(VENV)/bin/python' COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon $(COLCON_GLOBAL_ARGS) build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS) && source ros2_ws/install/setup.bash && COLCON_PYTHON_EXECUTABLE='$(CURDIR)/$(VENV)/bin/python' COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon $(COLCON_GLOBAL_ARGS) test $(COLCON_TEST_WS_ARGS) --event-handlers console_cohesion+ && COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon $(COLCON_GLOBAL_ARGS) test-result --test-result-base ros2_ws/build --verbose"

test: test-unit test-ros test-colcon

run:
	bash scripts/run_demo.sh

bench:
	bash scripts/run_benchmarks.sh

up: build
	ASR_RUNTIME_PROFILE=$(RUNTIME_PROFILE) ASR_PROVIDER_PROFILE=$(PROVIDER_PROFILE) bash scripts/run_web_ui.sh --mode $(GATEWAY_MODE) --stack $(GATEWAY_STACK) --port $(GATEWAY_PORT)

up-runtime: build
	bash scripts/run_web_ui.sh --stop --port $(GATEWAY_PORT)
	ASR_SKIP_BUILD=1 ASR_RUNTIME_PROFILE=$(RUNTIME_PROFILE) ASR_PROVIDER_PROFILE=$(PROVIDER_PROFILE) bash scripts/run_demo.sh

up-lan: build
	$(MAKE) up GATEWAY_MODE=lan

down:
	bash scripts/run_web_ui.sh --stop --port $(GATEWAY_PORT)

hf-smoke-local:
	bash -lc 'source $(VENV)/bin/activate && python3 scripts/run_huggingface_smoke.py --runtime-profile $(HF_LOCAL_RUNTIME_PROFILE) $(HF_SMOKE_ARGS)'

hf-smoke-api:
	bash -lc 'source $(VENV)/bin/activate && python3 scripts/run_huggingface_smoke.py --runtime-profile $(HF_API_RUNTIME_PROFILE) $(HF_SMOKE_ARGS)'

bench-hf:
	bash -lc 'source $(VENV)/bin/activate && python3 scripts/run_benchmark_core.py --benchmark-profile huggingface_provider_matrix --configs-root "$(CURDIR)/configs" --artifact-root "$(CURDIR)/artifacts" --registry-path "$(CURDIR)/datasets/registry/datasets.json" --results-dir "$(CURDIR)/results"'

rqt:
	bash scripts/run_rqt.sh $(RQT_ARGS)

report:
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) scripts/generate_report.py --input results/latest_benchmark_summary.json --output results/report.md'

web-gui:
	ASR_RUNTIME_PROFILE=$(RUNTIME_PROFILE) ASR_PROVIDER_PROFILE=$(PROVIDER_PROFILE) bash scripts/run_web_ui.sh --mode local --stack full

web-gui-lan:
	ASR_RUNTIME_PROFILE=$(RUNTIME_PROFILE) ASR_PROVIDER_PROFILE=$(PROVIDER_PROFILE) bash scripts/run_web_ui.sh --mode lan --stack full

web-gui-stop:
	bash scripts/run_web_ui.sh --stop --port 8088

arch-static:
	bash -lc "source $(VENV)/bin/activate && $(ARCHVIZ) static --ws ros2_ws --out docs/arch"

arch-runtime:
	bash -lc "source $(VENV)/bin/activate && if [ -f $(ROS_SETUP) ]; then source $(ROS_SETUP); [ -f ros2_ws/install/setup.bash ] && source ros2_ws/install/setup.bash || true; else echo 'ROS2 Jazzy setup not found at $(ROS_SETUP); runtime extractor will record it as runtime error.'; fi; $(ARCHVIZ) runtime --ws ros2_ws --out docs/arch --profile full --timeout-sec 20"

arch:
	bash -lc "source $(VENV)/bin/activate && if [ -f $(ROS_SETUP) ]; then source $(ROS_SETUP); [ -f ros2_ws/install/setup.bash ] && source ros2_ws/install/setup.bash || true; else echo 'ROS2 Jazzy setup not found at $(ROS_SETUP); runtime extractor will record it as runtime error.'; fi; $(ARCHVIZ) all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20"

arch-diff:
	bash -lc "source $(VENV)/bin/activate && $(ARCHVIZ) diff --a docs/arch/merged_graph_prev.json --b docs/arch/merged_graph.json --out docs/arch/CHANGELOG_ARCH.md"

lint-ruff:
	bash -lc "source $(VENV)/bin/activate && ruff check $(LINT_RUFF_PATHS)"

lint-mypy:
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) mypy $(LINT_MYPY_PATHS)'

lint: lint-ruff lint-mypy

security-scan:
	bash -lc 'source $(VENV)/bin/activate && bandit -q -r ros2_ws/src/asr_provider_base ros2_ws/src/asr_runtime_nodes ros2_ws/src/asr_datasets ros2_ws/src/asr_metrics/asr_observability ros2_ws/src/asr_benchmark_core/asr_benchmark_core'

format:
	bash -lc "source $(VENV)/bin/activate && ruff format ."

clean:
	rm -rf build install log ros2_ws/build ros2_ws/install ros2_ws/log \
		.pytest_cache .ruff_cache .mypy_cache dist
	rm -f results/benchmark_results.csv results/benchmark_results.json results/latest_benchmark_summary.json results/latest_benchmark_run.json results/report.md
	rm -rf results/plots
	find . -type d \( -path './.git' -o -path './.git/*' -o -path './.venv' -o -path './.venv/*' -o -path './.venv_*' -o -path './.venv_*/*' \) -prune -o -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d \( -path './.git' -o -path './.git/*' -o -path './.venv' -o -path './.venv/*' -o -path './.venv_*' -o -path './.venv_*/*' \) -prune -o -type f -name '*.pyc' -exec rm -f {} +

dist:
	$(MAKE) clean
	$(MAKE) test-unit
	$(MAKE) bench
	bash scripts/release_check.sh
	bash scripts/secret_scan.sh
	bash scripts/make_dist.sh

docsbot-setup:
	bash tools/docsbot/scripts/run_docsbot.sh detect > /dev/null || true

docsbot-detect:
	bash tools/docsbot/scripts/run_docsbot.sh detect --repo-root $(CURDIR)

docsbot-snapshot:
	bash tools/docsbot/scripts/run_docsbot.sh snapshot --repo-root $(CURDIR)

docsbot-generate:
	bash tools/docsbot/scripts/run_docsbot.sh generate --repo-root $(CURDIR)

docsbot-validate:
	bash tools/docsbot/scripts/run_docsbot.sh validate --repo-root $(CURDIR)

docsbot-watch:
	bash tools/docsbot/scripts/run_docsbot.sh watch --repo-root $(CURDIR)

docsbot-install-hooks:
	bash tools/docsbot/scripts/run_docsbot.sh install-hooks --repo-root $(CURDIR)
