#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Build workspace and run benchmark runner once.
source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

mkdir -p results/plots

# Keep colcon isolated from venv site-packages while preserving ROS python paths.
filter_colcon_pythonpath() {
  local current="${PYTHONPATH-}"
  local filtered=""
  local entry
  IFS=':' read -r -a entries <<< "$current"
  for entry in "${entries[@]}"; do
    [ -n "$entry" ] || continue
    if [ -n "${VIRTUAL_ENV:-}" ] && [[ "$entry" == "${VIRTUAL_ENV}"/* ]]; then
      continue
    fi
    if [ -n "$filtered" ]; then
      filtered="${filtered}:${entry}"
    else
      filtered="${entry}"
    fi
  done
  printf "%s" "$filtered"
}

ORIGINAL_PYTHONPATH="${PYTHONPATH-}"
COLCON_PYTHONPATH="$(filter_colcon_pythonpath)"
COLCON_PYTHON_BIN="${VIRTUAL_ENV:-}/bin/python"
if [ ! -x "$COLCON_PYTHON_BIN" ]; then
  COLCON_PYTHON_BIN="$(command -v python3)"
fi
if [ -n "$COLCON_PYTHONPATH" ]; then
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="$COLCON_PYTHONPATH" \
    bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
      --cmake-args -DPYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" -DPython3_EXECUTABLE="$COLCON_PYTHON_BIN"
else
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="" \
    bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
      --cmake-args -DPYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" -DPython3_EXECUTABLE="$COLCON_PYTHON_BIN"
fi
if [ -n "${ORIGINAL_PYTHONPATH}" ]; then
  export PYTHONPATH="${ORIGINAL_PYTHONPATH}"
else
  unset PYTHONPATH
fi
set +u
source "${ASR_COLCON_INSTALL_PREFIX}/setup.bash"
set -u

python3 scripts/run_benchmark_core.py \
  --benchmark-profile default_benchmark \
  --configs-root "$ROOT_DIR/configs" \
  --artifact-root "$ROOT_DIR/artifacts" \
  --registry-path "$ROOT_DIR/datasets/registry/datasets.json" \
  --results-dir "$ROOT_DIR/results"
