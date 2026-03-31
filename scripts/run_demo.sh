#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUNTIME_PROFILE="${ASR_RUNTIME_PROFILE:-default_runtime}"
PROVIDER_PROFILE="${ASR_PROVIDER_PROFILE:-providers/whisper_local}"
CANONICAL_SKIP_PACKAGES=(--packages-skip asr_ros asr_benchmark)

find_conflicting_managed_processes() {
  ps -eo pid=,comm=,args= \
    | awk -v root1="$ROOT_DIR/install/" -v root2="$ROOT_DIR/ros2_ws/install/" '
        (index($0, root1) || index($0, root2)) &&
        $2 ~ /^(python|python3|audio_input_nod|audio_preproces|vad_segmenter_n|asr_orchestrato|benchmark_manag|asr_gateway_ser)$/ &&
        $0 ~ /(audio_input_node|audio_preprocess_node|vad_segmenter_node|asr_orchestrator_node|benchmark_manager_node|asr_gateway_server)/ {
          pid = $1
          sub(/^[[:space:]]*[0-9]+[[:space:]]+[^[:space:]]+[[:space:]]+/, "", $0)
          print pid " " $0
        }
      '
}

CONFLICTS="$(find_conflicting_managed_processes)"
if [ -n "$CONFLICTS" ]; then
  echo "ERROR: Another managed ASR stack from this workspace is already running."
  echo "Stop it before launching runtime_minimal to avoid mixed ROS topics/services/logs."
  printf '%s\n' "$CONFLICTS"
  exit 1
fi

# Build workspace and start the current minimal runtime service surface.
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
COLCON_PYTHON_BIN="${VIRTUAL_ENV:-}/bin/python"
if [ ! -x "$COLCON_PYTHON_BIN" ]; then
  COLCON_PYTHON_BIN="$(command -v python3)"
fi
if [ -n "$COLCON_PYTHONPATH" ]; then
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="$COLCON_PYTHONPATH" \
    bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
      "${CANONICAL_SKIP_PACKAGES[@]}" \
      --cmake-args -DPYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" -DPython3_EXECUTABLE="$COLCON_PYTHON_BIN"
else
  COLCON_PYTHON_EXECUTABLE="$COLCON_PYTHON_BIN" \
    PYTHONPATH="" \
    bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
      "${CANONICAL_SKIP_PACKAGES[@]}" \
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
ros2 launch asr_launch runtime_minimal.launch.py \
  runtime_profile:="$RUNTIME_PROFILE" \
  provider_profile:="$PROVIDER_PROFILE"
