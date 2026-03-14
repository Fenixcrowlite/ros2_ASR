SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
ROS_SETUP := /opt/ros/jazzy/setup.bash
SRC_PY_PATH := $(shell find $(CURDIR)/ros2_ws/src -mindepth 1 -maxdepth 1 -type d | tr '\n' ':')
PY_PATH := $(CURDIR):$(SRC_PY_PATH)
ARCHVIZ := ./archviz
COLCON_CMAKE_PY_ARGS := --cmake-args -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPython3_EXECUTABLE=/usr/bin/python3
COLCON_EXTENSION_BLOCKLIST ?= colcon_core.event_handler.desktop_notification
COLCON_WS_ARGS := --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --log-base ros2_ws/log --symlink-install

.PHONY: setup build test test-unit test-ros test-colcon run live-sample bench report web-gui web-gui-lan web-gui-stop web-gui-legacy web-gui-legacy-lan arch-static arch-runtime arch arch-diff lint format clean dist docsbot-setup docsbot-detect docsbot-snapshot docsbot-generate docsbot-validate docsbot-watch docsbot-install-hooks

setup:
	bash scripts/setup_env.sh

build:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP).'; exit 1; fi; if [ ! -f $(VENV)/bin/activate ]; then echo '.venv missing. Run make setup first.'; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS)"

test-unit:
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) -m pytest -q -m "not ros"'

test-ros:
	bash -lc 'if [ ! -f $(ROS_SETUP) ]; then echo "ROS2 Jazzy not found at $(ROS_SETUP), skipping ROS tests."; exit 0; fi; if [ ! -f $(VENV)/bin/activate ]; then echo ".venv missing. Run make setup first."; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_EXTENSION_BLOCKLIST="$(COLCON_EXTENSION_BLOCKLIST)" bash scripts/with_colcon_lock.sh colcon build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS) && source ros2_ws/install/setup.bash && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) -m pytest -q -m ros tests/integration'

test-colcon:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP), skipping colcon tests.'; exit 0; fi; if [ ! -f $(VENV)/bin/activate ]; then echo '.venv missing. Run make setup first.'; exit 1; fi; source $(VENV)/bin/activate && source $(ROS_SETUP) && COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon build $(COLCON_WS_ARGS) $(COLCON_CMAKE_PY_ARGS) && source ros2_ws/install/setup.bash && COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon test $(COLCON_WS_ARGS) --event-handlers console_cohesion+ && COLCON_EXTENSION_BLOCKLIST='$(COLCON_EXTENSION_BLOCKLIST)' bash scripts/with_colcon_lock.sh colcon test-result --test-result-base ros2_ws/build --verbose"

test: test-unit test-ros test-colcon

run:
	bash scripts/run_demo.sh

live-sample:
	bash scripts/run_live_sample_eval.sh

bench:
	bash scripts/run_benchmarks.sh

report:
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) $(PY) scripts/generate_report.py --input results/benchmark_results.json --output results/report.md'

web-gui:
	bash scripts/run_web_ui.sh --mode local --stack full

web-gui-lan:
	bash scripts/run_web_ui.sh --mode lan --stack full

web-gui-stop:
	bash scripts/run_web_ui.sh --stop --port 8088

web-gui-legacy:
	bash web_gui/run_web_gui.sh --mode local

web-gui-legacy-lan:
	bash web_gui/run_web_gui.sh --mode lan

arch-static:
	bash -lc "source $(VENV)/bin/activate && $(ARCHVIZ) static --ws ros2_ws --out docs/arch"

arch-runtime:
	bash -lc "source $(VENV)/bin/activate && if [ -f $(ROS_SETUP) ]; then source $(ROS_SETUP); [ -f ros2_ws/install/setup.bash ] && source ros2_ws/install/setup.bash || true; else echo 'ROS2 Jazzy setup not found at $(ROS_SETUP); runtime extractor will record it as runtime error.'; fi; $(ARCHVIZ) runtime --ws ros2_ws --out docs/arch --profile full --timeout-sec 20"

arch:
	bash -lc "source $(VENV)/bin/activate && if [ -f $(ROS_SETUP) ]; then source $(ROS_SETUP); [ -f ros2_ws/install/setup.bash ] && source ros2_ws/install/setup.bash || true; else echo 'ROS2 Jazzy setup not found at $(ROS_SETUP); runtime extractor will record it as runtime error.'; fi; $(ARCHVIZ) all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20"

arch-diff:
	bash -lc "source $(VENV)/bin/activate && $(ARCHVIZ) diff --a docs/arch/merged_graph_prev.json --b docs/arch/merged_graph.json --out docs/arch/CHANGELOG_ARCH.md"

lint:
	bash -lc "source $(VENV)/bin/activate && ruff check ."
	bash -lc 'source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(PY_PATH) mypy ros2_ws/src tests web_gui scripts tools/archviz'

format:
	bash -lc "source $(VENV)/bin/activate && ruff format ."

clean:
	rm -rf build install log ros2_ws/build ros2_ws/install ros2_ws/log \
		.pytest_cache .ruff_cache .mypy_cache dist
	rm -f results/benchmark_results.csv results/benchmark_results.json results/report.md
	rm -rf results/plots results/web_gui
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
