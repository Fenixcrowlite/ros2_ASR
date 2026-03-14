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

if [[ "$MIC_CAPTURE_SEC" =~ ^-?[0-9]+$ ]]; then
  MIC_CAPTURE_SEC="${MIC_CAPTURE_SEC}.0"
fi

if [ ! -f "$ROOT_DIR/.venv/bin/activate" ]; then
  echo "ERROR: .venv is missing. Run: make setup"
  exit 1
fi

if [ ! -f "/opt/ros/jazzy/setup.bash" ]; then
  echo "ERROR: ROS2 Jazzy not found at /opt/ros/jazzy/setup.bash"
  exit 1
fi

if [ ! -f "${ASR_COLCON_INSTALL_PREFIX:-$ROOT_DIR/ros2_ws/install}/setup.bash" ]; then
  echo "${ASR_COLCON_INSTALL_PREFIX:-$ROOT_DIR/ros2_ws/install}/setup.bash not found. Building workspace first..."
  source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros
  cd "$ROOT_DIR"
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
  if [ -n "${COLCON_PYTHONPATH}" ]; then
    COLCON_PYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" \
      PYTHONPATH="${COLCON_PYTHONPATH}" \
      bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --log-base ros2_ws/log --symlink-install \
        --cmake-args -DPYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" -DPython3_EXECUTABLE="${COLCON_PYTHON_BIN}"
  else
    COLCON_PYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" \
      PYTHONPATH="" \
      bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --log-base ros2_ws/log --symlink-install \
        --cmake-args -DPYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" -DPython3_EXECUTABLE="${COLCON_PYTHON_BIN}"
  fi
  if [ -n "${ORIGINAL_PYTHONPATH}" ]; then
    export PYTHONPATH="${ORIGINAL_PYTHONPATH}"
  else
    unset PYTHONPATH
  fi
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
source scripts/source_runtime_env.sh --with-ros
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
