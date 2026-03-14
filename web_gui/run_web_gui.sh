#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/source_runtime_env.sh" --without-ros

mode="local"
host_override=""
port_override=""
open_browser=1
auto_port="${WEB_GUI_AUTO_PORT:-1}"

usage() {
  cat <<'EOF'
Usage:
  bash web_gui/run_web_gui.sh [--mode local|lan] [--host HOST] [--port PORT] [--no-open]

Defaults:
  mode=local -> host=127.0.0.1, port=8765
  mode=lan   -> host=0.0.0.0, port=8765

Env overrides:
  WEB_GUI_HOST, WEB_GUI_PORT, WEB_GUI_AUTO_PORT
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      mode="${2:-}"
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
    --no-open)
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

if [[ -n "$host_override" ]]; then
  HOST="$host_override"
elif [[ -n "${WEB_GUI_HOST:-}" ]]; then
  HOST="${WEB_GUI_HOST}"
elif [[ "$mode" == "lan" ]]; then
  HOST="0.0.0.0"
else
  HOST="127.0.0.1"
fi

if [[ -n "$port_override" ]]; then
  PORT="$port_override"
elif [[ -n "${WEB_GUI_PORT:-}" ]]; then
  PORT="${WEB_GUI_PORT}"
else
  PORT="8765"
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || ((PORT < 1 || PORT > 65535)); then
  echo "Invalid port: $PORT" >&2
  exit 1
fi

is_port_free() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

if [[ "$auto_port" == "1" ]]; then
  base_port="$PORT"
  if ! is_port_free "$HOST" "$PORT"; then
    for candidate in $(seq $((base_port + 1)) $((base_port + 100))); do
      if is_port_free "$HOST" "$candidate"; then
        PORT="$candidate"
        break
      fi
    done
  fi
fi

if ! is_port_free "$HOST" "$PORT"; then
  echo "Port $PORT on $HOST is busy. Set WEB_GUI_PORT or pass --port." >&2
  exit 1
fi

BROWSER_HOST="$HOST"
if [[ "$BROWSER_HOST" == "0.0.0.0" ]]; then
  BROWSER_HOST="127.0.0.1"
fi
URL="http://${BROWSER_HOST}:${PORT}"

echo "Starting Web GUI on ${HOST}:${PORT}"
echo "Open: ${URL}"

if [[ "$HOST" == "0.0.0.0" ]]; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "$LAN_IP" ]]; then
    echo "LAN:  http://${LAN_IP}:${PORT}"
  fi
fi

if [[ "$open_browser" == "1" ]]; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 || true
  elif command -v gio >/dev/null 2>&1; then
    gio open "$URL" >/dev/null 2>&1 || true
  fi
fi

python3 -m uvicorn web_gui.app.main:app --host "$HOST" --port "$PORT" --reload
