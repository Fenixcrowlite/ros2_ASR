#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Build workspace and start demo launch with default profile.
source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

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
COLCON_PYTHON_BIN="/usr/bin/python3"
if [ ! -x "$COLCON_PYTHON_BIN" ]; then
  COLCON_PYTHON_BIN="$(command -v python3)"
fi
if [ -n "$COLCON_PYTHONPATH" ]; then
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="$COLCON_PYTHONPATH" \
    colcon build --base-paths ros2_ws/src --symlink-install \
      --cmake-args -DPYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" -DPython3_EXECUTABLE="$COLCON_PYTHON_BIN"
else
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="" \
    colcon build --base-paths ros2_ws/src --symlink-install \
      --cmake-args -DPYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" -DPython3_EXECUTABLE="$COLCON_PYTHON_BIN"
fi
if [ -n "${ORIGINAL_PYTHONPATH}" ]; then
  export PYTHONPATH="${ORIGINAL_PYTHONPATH}"
else
  unset PYTHONPATH
fi
set +u
source install/setup.bash
set -u
ros2 launch asr_ros demo.launch.py config:=configs/default.yaml
