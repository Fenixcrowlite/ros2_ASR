#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

rm -rf \
  .pytest_cache \
  .ruff_cache \
  ros2_ws/build \
  ros2_ws/install \
  ros2_ws/log

rm -f \
  .coverage \
  .colcon.lock

find . \
  -path './.git' -prune -o \
  -path './.venv' -prune -o \
  -path './.venv_*' -prune -o \
  -type d -name '__pycache__' -prune -print -exec rm -rf {} +

if [ -d artifacts/temp ]; then
  find artifacts/temp -mindepth 1 -maxdepth 1 -type d -print -exec rm -rf {} +
fi
