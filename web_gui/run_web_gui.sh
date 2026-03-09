#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/source_runtime_env.sh" --without-ros

HOST="${WEB_GUI_HOST:-0.0.0.0}"
PORT="${WEB_GUI_PORT:-8765}"

python3 -m uvicorn web_gui.app.main:app --host "$HOST" --port "$PORT" --reload
