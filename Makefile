SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
ROS_SETUP := /opt/ros/jazzy/setup.bash
SRC_PY_PATH := $(shell find $(PWD)/ros2_ws/src -mindepth 1 -maxdepth 1 -type d | tr '\n' ':')

.PHONY: setup build test test-unit test-ros test-colcon run bench report lint format clean dist

setup:
	bash scripts/setup_env.sh

build:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP).'; exit 1; fi; source $(ROS_SETUP) && colcon build --base-paths ros2_ws/src --symlink-install"

test-unit:
	bash -lc "source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(SRC_PY_PATH) pytest -q -m 'not ros'"

test-ros:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP), skipping ROS tests.'; exit 0; fi; source $(ROS_SETUP) && colcon build --base-paths ros2_ws/src --symlink-install && source install/setup.bash && source $(VENV)/bin/activate && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -m ros"

test-colcon:
	bash -lc "if [ ! -f $(ROS_SETUP) ]; then echo 'ROS2 Jazzy not found at $(ROS_SETUP), skipping colcon tests.'; exit 0; fi; source $(ROS_SETUP) && colcon build --base-paths ros2_ws/src --symlink-install && source install/setup.bash && colcon test --base-paths ros2_ws/src --event-handlers console_cohesion+ && colcon test-result --verbose"

test: test-unit test-ros test-colcon

run:
	bash scripts/run_demo.sh

bench:
	bash scripts/run_benchmarks.sh

report:
	bash -lc "source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(SRC_PY_PATH) $(PY) scripts/generate_report.py --input results/benchmark_results.json --output results/report.md"

lint:
	bash -lc "source $(VENV)/bin/activate && ruff check ."
	bash -lc "source $(VENV)/bin/activate && PYTHONPATH=$$PYTHONPATH:$(SRC_PY_PATH) mypy ros2_ws/src tests"

format:
	bash -lc "source $(VENV)/bin/activate && ruff format ."

clean:
	rm -rf build install log ros2_ws/build ros2_ws/install ros2_ws/log \
		.pytest_cache .ruff_cache .mypy_cache results dist
	find . -type d \( -path './.git' -o -path './.git/*' -o -path './.venv' -o -path './.venv/*' -o -path './.venv_*' -o -path './.venv_*/*' \) -prune -o -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d \( -path './.git' -o -path './.git/*' -o -path './.venv' -o -path './.venv/*' -o -path './.venv_*' -o -path './.venv_*/*' \) -prune -o -type f -name '*.pyc' -exec rm -f {} +

dist:
	$(MAKE) clean
	$(MAKE) test-unit
	$(MAKE) bench
	bash scripts/release_check.sh
	bash scripts/secret_scan.sh
	bash scripts/make_dist.sh
