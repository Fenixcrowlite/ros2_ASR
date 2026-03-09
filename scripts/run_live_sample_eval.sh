#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .venv/bin/activate ]; then
  echo "ERROR: .venv is missing. Run: make setup"
  exit 1
fi

source "$ROOT_DIR/scripts/source_runtime_env.sh" --without-ros

if [ -f /opt/ros/jazzy/setup.bash ]; then
  set +u
  source /opt/ros/jazzy/setup.bash
  [ -f install/setup.bash ] && source install/setup.bash || true
  set -u
fi

if [ "$#" -eq 0 ]; then
  python3 scripts/live_sample_eval.py --interactive
else
  python3 scripts/live_sample_eval.py "$@"
fi
