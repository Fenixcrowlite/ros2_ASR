#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Build workspace and start demo launch with default profile.
source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

# Keep colcon isolated from venv site-packages injected via PYTHONPATH.
COLCON_PYTHONPATH="${PYTHONPATH-}"
PYTHONPATH="" colcon build --base-paths ros2_ws/src --symlink-install
if [ -n "${COLCON_PYTHONPATH}" ]; then
  export PYTHONPATH="${COLCON_PYTHONPATH}"
else
  unset PYTHONPATH
fi
set +u
source install/setup.bash
set -u
ros2 launch asr_ros demo.launch.py config:=configs/default.yaml
