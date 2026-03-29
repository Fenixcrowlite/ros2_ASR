#!/usr/bin/env bash
set -euo pipefail

# Opens two terminals for current runtime stack testing:
# 1) runtime launch
# 2) final-result topic echo + start_session call

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUNTIME_PROFILE="${1:-default_runtime}"
INPUT_MODE="${2:-mic}"
PROVIDER_PROFILE="${3:-providers/whisper_local}"
MIC_CAPTURE_SEC="${4:-6.0}"
AUDIO_FILE_PATH="${5:-data/sample/vosk_test.wav}"
LANGUAGE="${ASR_LANGUAGE:-en-US}"
PROCESSING_MODE="${ASR_PROCESSING_MODE:-segmented}"
DRY_RUN="${DRY_RUN:-false}"

if [[ "$MIC_CAPTURE_SEC" =~ ^-?[0-9]+$ ]]; then
  MIC_CAPTURE_SEC="${MIC_CAPTURE_SEC}.0"
fi

if [[ "$INPUT_MODE" != "mic" && "$INPUT_MODE" != "file" ]]; then
  echo "ERROR: INPUT_MODE must be one of: mic, file"
  exit 1
fi

if [[ "$PROCESSING_MODE" != "segmented" && "$PROCESSING_MODE" != "provider_stream" ]]; then
  echo "ERROR: PROCESSING_MODE must be one of: segmented, provider_stream"
  exit 1
fi

if [[ "$INPUT_MODE" == "file" && ! -f "$ROOT_DIR/$AUDIO_FILE_PATH" && ! -f "$AUDIO_FILE_PATH" ]]; then
  echo "ERROR: audio file not found: $AUDIO_FILE_PATH"
  exit 1
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
  COLCON_PYTHON_BIN="${VIRTUAL_ENV:-}/bin/python"
  if [ ! -x "$COLCON_PYTHON_BIN" ]; then
    COLCON_PYTHON_BIN="$(command -v python3)"
  fi
  if [ -n "${COLCON_PYTHONPATH}" ]; then
    COLCON_PYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" \
      PYTHONPATH="${COLCON_PYTHONPATH}" \
      bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
        --cmake-args -DPYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" -DPython3_EXECUTABLE="${COLCON_PYTHON_BIN}"
  else
    COLCON_PYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" \
      PYTHONPATH="" \
      bash "$ROOT_DIR/scripts/with_colcon_lock.sh" colcon --log-base ros2_ws/log build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install \
        --cmake-args -DPYTHON_EXECUTABLE="${COLCON_PYTHON_BIN}" -DPython3_EXECUTABLE="${COLCON_PYTHON_BIN}"
  fi
  if [ -n "${ORIGINAL_PYTHONPATH}" ]; then
    export PYTHONPATH="${ORIGINAL_PYTHONPATH}"
  else
    unset PYTHONPATH
  fi
fi

source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros >/dev/null 2>&1

if [[ "$PROCESSING_MODE" == "provider_stream" ]]; then
  if ! python3 - "$PROVIDER_PROFILE" <<'PY'
import sys

from asr_provider_base import ProviderManager

profile = sys.argv[1]
manager = ProviderManager(configs_root="configs")
provider = manager.create_from_profile(profile)
try:
    sys.exit(0 if provider.discover_capabilities().supports_streaming else 2)
finally:
    provider.teardown()
PY
  then
    echo "ERROR: provider profile does not support provider_stream: $PROVIDER_PROFILE"
    exit 1
  fi
fi

if ! command -v gnome-terminal >/dev/null 2>&1; then
  echo "ERROR: gnome-terminal is not installed."
  echo "Run these two commands manually in separate terminals:"
  echo "  1) ros2 launch asr_launch runtime_streaming.launch.py runtime_profile:=$RUNTIME_PROFILE provider_profile:=$PROVIDER_PROFILE input_mode:=$INPUT_MODE"
  echo "  2) ros2 topic echo /asr/runtime/results/final --qos-durability transient_local --qos-reliability reliable"
  echo "     and then call /asr/runtime/start_session with audio_source:=$INPUT_MODE"
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
ros2 launch asr_launch runtime_streaming.launch.py runtime_profile:=\"$RUNTIME_PROFILE\" provider_profile:=\"$PROVIDER_PROFILE\" input_mode:=\"$INPUT_MODE\""

TOPIC_CMD="$COMMON_SETUP
ros2 topic echo /asr/runtime/results/final --qos-durability transient_local --qos-reliability reliable &
topic_pid=\$!
cleanup() {
  kill \"\$topic_pid\" 2>/dev/null || true
  wait \"\$topic_pid\" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

service_ready=0
for _ in {1..60}; do
  if ros2 service type /asr/runtime/start_session >/dev/null 2>&1; then
    service_ready=1
    break
  fi
  sleep 0.5
done

if [ \"\$service_ready\" -ne 1 ]; then
  echo 'ERROR: /asr/runtime/start_session did not become available in time.' >&2
  exit 1
fi

ros2 service call /asr/runtime/start_session asr_interfaces/srv/StartRuntimeSession \"{runtime_profile: '$RUNTIME_PROFILE', provider_profile: '$PROVIDER_PROFILE', provider_preset: '', provider_settings_json: '{}', session_id: '', runtime_namespace: '/asr/runtime', auto_start_audio: true, processing_mode: '$PROCESSING_MODE', audio_source: '$INPUT_MODE', audio_file_path: '$AUDIO_FILE_PATH', language: '$LANGUAGE', mic_capture_sec: $MIC_CAPTURE_SEC}\"
wait \"\$topic_pid\""

if [ "$DRY_RUN" = "true" ]; then
  echo "===== Terminal 1 (recognition) ====="
  echo "$RECOGNITION_CMD"
  echo
  echo "===== Terminal 2 (topic echo) ====="
  echo "$TOPIC_CMD"
  exit 0
fi

echo "Opening terminals..."
gnome-terminal --title="ASR Runtime Launch" -- bash -lc "$RECOGNITION_CMD; exec bash"
sleep 1
gnome-terminal --title="ASR Final Results" -- bash -lc "$TOPIC_CMD; exec bash"

echo "Done."
