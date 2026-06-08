#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

mode="local"
stack="full"
open_browser=1
host_override=""
port_override=""
action="start"
runtime_profile="${ASR_RUNTIME_PROFILE:-default_runtime}"
provider_profile="${ASR_PROVIDER_PROFILE:-providers/whisper_local}"
configs_root="${ASR_CONFIGS_ROOT:-configs}"
artifacts_root="${ASR_ARTIFACTS_ROOT:-artifacts}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_web_ui.sh [--mode local|lan] [--stack full|runtime] [--host HOST] [--port PORT] [--runtime-profile ID] [--provider-profile ID] [--configs-root PATH] [--artifacts-root PATH] [--no-open]
  bash scripts/run_web_ui.sh --stop [--port PORT]

Defaults:
  mode=local -> host=127.0.0.1, port=8088
  mode=lan   -> host=0.0.0.0, port=8088
  stack=full -> asr_launch/full_stack_dev.launch.py
  stack=runtime -> asr_launch/gateway_with_runtime.launch.py
  runtime_profile=default_runtime
  provider_profile=providers/whisper_local
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --stack)
      stack="${2:-}"
      shift 2
      ;;
    --host)
      host_override="${2:-}"
      shift 2
      ;;
    --port)
      port_override="${2:-}"
      shift 2
      ;;
    --runtime-profile)
      runtime_profile="${2:-}"
      shift 2
      ;;
    --provider-profile)
      provider_profile="${2:-}"
      shift 2
      ;;
    --configs-root)
      configs_root="${2:-}"
      shift 2
      ;;
    --artifacts-root)
      artifacts_root="${2:-}"
      shift 2
      ;;
    --no-open)
      open_browser=0
      shift
      ;;
    --stop)
      action="stop"
      open_browser=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$mode" != "local" && "$mode" != "lan" ]]; then
  echo "Invalid mode: $mode (expected local or lan)" >&2
  exit 1
fi

if [[ "$stack" != "full" && "$stack" != "runtime" ]]; then
  echo "Invalid stack: $stack (expected full or runtime)" >&2
  exit 1
fi

if [[ -z "$runtime_profile" ]]; then
  echo "Invalid runtime_profile: must not be empty" >&2
  exit 1
fi

if [[ -z "$provider_profile" ]]; then
  echo "Invalid provider_profile: must not be empty" >&2
  exit 1
fi

if [[ -n "$host_override" ]]; then
  GATEWAY_HOST="$host_override"
elif [[ "$mode" == "lan" ]]; then
  GATEWAY_HOST="0.0.0.0"
else
  GATEWAY_HOST="127.0.0.1"
fi

if [[ -n "$port_override" ]]; then
  GATEWAY_PORT="$port_override"
else
  GATEWAY_PORT="8088"
fi

if ! [[ "$GATEWAY_PORT" =~ ^[0-9]+$ ]] || ((GATEWAY_PORT < 1 || GATEWAY_PORT > 65535)); then
  echo "Invalid port: $GATEWAY_PORT" >&2
  exit 1
fi

INSTALL_PREFIX="${ASR_COLCON_INSTALL_PREFIX:-$ROOT_DIR/ros2_ws/install}"

if [[ ! -f "$INSTALL_PREFIX/setup.bash" ]]; then
  echo "ERROR: ${INSTALL_PREFIX}/setup.bash not found. Run: make build" >&2
  exit 1
fi

find_existing_launch_pids() {
  ps -eo pid=,comm=,args= \
    | awk -v port_arg="gateway_port:=$GATEWAY_PORT" '
        $2 == "ros2" && index($0, "ros2 launch asr_launch") && index($0, port_arg) { print $1 }
      '
}

find_listener_pids() {
  lsof -t -iTCP:"$GATEWAY_PORT" -sTCP:LISTEN -n -P 2>/dev/null || true
}

find_managed_node_pids() {
  ps -eo pid=,comm=,args= \
    | awk -v root1="$ROOT_DIR/install/" -v root2="$ROOT_DIR/ros2_ws/install/" '
        (index($0, root1) || index($0, root2)) &&
        $2 ~ /^(audio_input_nod|audio_preproces|vad_segmenter_n|asr_orchestrato|benchmark_manag|asr_gateway_ser)$/ &&
        $0 ~ /(audio_input_node|audio_preprocess_node|vad_segmenter_node|asr_orchestrator_node|benchmark_manager_node|asr_gateway_server)/ {
          print $1
        }
      ' \
    | sort -u
}

pid_args() {
  ps -p "$1" -o args= 2>/dev/null || true
}

stop_pid_gracefully() {
  local pid="$1"
  local label="$2"
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi

  echo "Stopping ${label} (pid ${pid})"
  kill -TERM "$pid" 2>/dev/null || true
  for _ in {1..30}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 0.2
  done

  echo "Force stopping ${label} (pid ${pid})"
  kill -KILL "$pid" 2>/dev/null || true
}

stop_existing_stack_on_port() {
  local found_managed=0
  local pid=""

  while read -r pid; do
    [[ -z "$pid" ]] && continue
    found_managed=1
    stop_pid_gracefully "$pid" "existing web UI launch on port ${GATEWAY_PORT}"
  done < <(find_existing_launch_pids)

  while read -r pid; do
    [[ -z "$pid" ]] && continue
    local args
    args="$(pid_args "$pid")"
    if [[ "$args" == *"asr_gateway_server"* ]]; then
      found_managed=1
      stop_pid_gracefully "$pid" "orphan gateway on port ${GATEWAY_PORT}"
      continue
    fi
    echo "ERROR: Port ${GATEWAY_PORT} is already in use by an unrelated process:" >&2
    echo "  PID ${pid}: ${args}" >&2
    return 1
  done < <(find_listener_pids)

  while read -r pid; do
    [[ -z "$pid" ]] && continue
    found_managed=1
    stop_pid_gracefully "$pid" "managed ROS node"
  done < <(find_managed_node_pids)

  if [[ "$found_managed" == "1" ]]; then
    for _ in {1..30}; do
      if [[ -z "$(find_listener_pids)" && -z "$(find_managed_node_pids)" ]]; then
        break
      fi
      sleep 0.2
    done
  fi

  while read -r pid; do
    [[ -z "$pid" ]] && continue
    stop_pid_gracefully "$pid" "surviving managed ROS node"
  done < <(find_managed_node_pids)

  if [[ "$found_managed" == "1" ]]; then
    for _ in {1..20}; do
      if [[ -z "$(find_listener_pids)" && -z "$(find_managed_node_pids)" ]]; then
        break
      fi
      sleep 0.2
    done
  fi

  if [[ -n "$(find_listener_pids)" || -n "$(find_managed_node_pids)" ]]; then
    echo "ERROR: Previous managed stack processes are still alive after stop." >&2
    return 1
  fi

  return 0
}

LAUNCH_FILE="full_stack_dev.launch.py"
if [[ "$stack" == "runtime" ]]; then
  LAUNCH_FILE="gateway_with_runtime.launch.py"
fi

BROWSER_HOST="$GATEWAY_HOST"
if [[ "$BROWSER_HOST" == "0.0.0.0" ]]; then
  BROWSER_HOST="127.0.0.1"
fi
URL="http://${BROWSER_HOST}:${GATEWAY_PORT}"

if [[ "$action" == "stop" ]]; then
  stop_existing_stack_on_port
  echo "Web UI stack on port ${GATEWAY_PORT} is stopped"
  exit 0
fi

stop_existing_stack_on_port

echo "Starting new web UI stack"
echo "Launch: asr_launch/${LAUNCH_FILE}"
echo "Gateway: ${GATEWAY_HOST}:${GATEWAY_PORT}"
echo "Runtime profile: ${runtime_profile}"
echo "Provider profile: ${provider_profile}"
if [[ "$stack" == "full" ]]; then
  echo "Configs root: ${configs_root}"
  echo "Artifacts root: ${artifacts_root}"
fi
echo "Open: ${URL}"

if [[ "$GATEWAY_HOST" == "0.0.0.0" ]]; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "$LAN_IP" ]]; then
    echo "LAN:  http://${LAN_IP}:${GATEWAY_PORT}"
  fi
fi

if [[ "$open_browser" == "1" ]]; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 || true
  elif command -v gio >/dev/null 2>&1; then
    gio open "$URL" >/dev/null 2>&1 || true
  fi
fi

export ASR_PROJECT_ROOT="$ROOT_DIR"
if [[ "$stack" == "full" ]]; then
  ros2 launch asr_launch "$LAUNCH_FILE" \
    runtime_profile:="$runtime_profile" \
    provider_profile:="$provider_profile" \
    gateway_host:="$GATEWAY_HOST" \
    gateway_port:="$GATEWAY_PORT" \
    configs_root:="$configs_root" \
    artifacts_root:="$artifacts_root"
else
  ros2 launch asr_launch "$LAUNCH_FILE" \
    runtime_profile:="$runtime_profile" \
    provider_profile:="$provider_profile" \
    gateway_host:="$GATEWAY_HOST" \
    gateway_port:="$GATEWAY_PORT"
fi
