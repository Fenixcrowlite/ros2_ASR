#!/usr/bin/env bash
set -euo pipefail

# Build workspace and start demo launch with default profile.
set +u
source /opt/ros/jazzy/setup.bash
set -u

colcon build --base-paths ros2_ws/src --symlink-install
set +u
source install/setup.bash
set -u
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

ros2 launch asr_ros demo.launch.py config:=configs/default.yaml
