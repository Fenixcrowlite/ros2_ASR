#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

export PYTHONPATH="${PYTHONPATH:-}:$(find "$ROOT_DIR/ros2_ws/src" -mindepth 1 -maxdepth 1 -type d | tr '\n' ':')"

HOST="${WEB_GUI_HOST:-0.0.0.0}"
PORT="${WEB_GUI_PORT:-8765}"

python3 -m uvicorn web_gui.app.main:app --host "$HOST" --port "$PORT" --reload
