#!/usr/bin/env bash
set -euo pipefail

# Opens two terminals for live ASR testing:
# 1) ASR pipeline launch (mic/file -> backend -> topics)
# 2) Topic echo for plain recognized text (/asr/text/plain)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CONFIG="${1:-configs/live_mic_whisper.yaml}"
INPUT_MODE="${2:-mic}"
CONTINUOUS="${3:-true}"
MIC_CAPTURE_SEC="${4:-6.0}"
DRY_RUN="${DRY_RUN:-false}"

if [ ! -f "$ROOT_DIR/.venv/bin/activate" ]; then
  echo "ERROR: .venv is missing. Run: make setup"
  exit 1
fi

if [ ! -f "/opt/ros/jazzy/setup.bash" ]; then
  echo "ERROR: ROS2 Jazzy not found at /opt/ros/jazzy/setup.bash"
  exit 1
fi

if [ ! -f "$ROOT_DIR/install/setup.bash" ]; then
  echo "install/setup.bash not found. Building workspace first..."
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
  cd "$ROOT_DIR"
  colcon build --base-paths ros2_ws/src --symlink-install
fi

if ! command -v gnome-terminal >/dev/null 2>&1; then
  echo "ERROR: gnome-terminal is not installed."
  echo "Run these two commands manually in separate terminals:"
  echo "  1) ros2 launch asr_ros bringup.launch.py config:=$CONFIG input_mode:=$INPUT_MODE continuous:=$CONTINUOUS mic_capture_sec:=$MIC_CAPTURE_SEC"
  echo "  2) ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable"
  exit 1
fi

COMMON_SETUP=$(cat <<EOF_SETUP
cd "$ROOT_DIR"
source .venv/bin/activate
export PYTHONPATH="\$(python -c 'import site; print(site.getsitepackages()[0])'):\${PYTHONPATH:-}"
export LD_LIBRARY_PATH="\$(
python - <<'PY'
import glob
import os
import site

paths = []
for base in site.getsitepackages():
    paths += glob.glob(os.path.join(base, "nvidia", "*", "lib"))
print(":".join(paths))
PY
):\${LD_LIBRARY_PATH:-}"
set +u
source /opt/ros/jazzy/setup.bash
source install/setup.bash
set -u
EOF_SETUP
)

RECOGNITION_CMD="$COMMON_SETUP
ros2 launch asr_ros bringup.launch.py config:=\"$CONFIG\" input_mode:=\"$INPUT_MODE\" continuous:=\"$CONTINUOUS\" mic_capture_sec:=\"$MIC_CAPTURE_SEC\""

TOPIC_CMD="$COMMON_SETUP
ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable"

if [ "$DRY_RUN" = "true" ]; then
  echo "===== Terminal 1 (recognition) ====="
  echo "$RECOGNITION_CMD"
  echo
  echo "===== Terminal 2 (topic echo) ====="
  echo "$TOPIC_CMD"
  exit 0
fi

echo "Opening terminals..."
gnome-terminal --title="ASR Recognition" -- bash -lc "$RECOGNITION_CMD; exec bash"
sleep 1
gnome-terminal --title="ASR Text Topic" -- bash -lc "$TOPIC_CMD; exec bash"

echo "Done."
