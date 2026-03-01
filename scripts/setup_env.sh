#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Create local virtual environment and install Python dependencies.
if [ ! -d .venv ]; then
  if ! python3 -m venv .venv 2>/dev/null; then
    echo "python3 -m venv failed, trying virtualenv fallback"
    python3 -m pip install --user --break-system-packages virtualenv
    python3 -m virtualenv .venv
  fi
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ln -sf "$(pwd)/archviz" .venv/bin/archviz

echo "Environment ready. Activate with: source .venv/bin/activate"
