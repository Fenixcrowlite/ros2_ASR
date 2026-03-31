#!/usr/bin/env bash
set -euo pipefail

# Package sterile release archive with required source/docs/results artifacts.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d "results/plots" ]; then
  echo "ERROR: results/plots is missing. Run make bench first."
  exit 1
fi

PLOT_COUNT=$(find results/plots -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')
if [ "$PLOT_COUNT" -lt 3 ]; then
  echo "ERROR: expected at least 3 plots in results/plots, found $PLOT_COUNT"
  exit 1
fi

mkdir -p dist
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="dist/ros2_asr_release_${TIMESTAMP}.tar.gz"

tar -czf "$ARCHIVE" \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='.venv_*' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  --exclude='.mypy_cache' \
  --exclude='build' \
  --exclude='install' \
  --exclude='log' \
  --exclude='ros2_ws/build' \
  --exclude='ros2_ws/install' \
  --exclude='ros2_ws/log' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='configs/commercial.yaml' \
  --exclude='*.env' \
  --exclude='.env' \
  --exclude='*.pem' \
  --exclude='*.key' \
  --exclude='*.p12' \
  README.md \
  Makefile \
  pyproject.toml \
  requirements.txt \
  requirements \
  docs \
  ros2_ws/src \
  scripts \
  data/sample \
  data/transcripts \
  configs \
  tests \
  results

echo "Archive: $ARCHIVE"
echo "Size: $(du -h "$ARCHIVE" | awk '{print $1}')"
echo "Top-level entries:"
tar -tzf "$ARCHIVE" | awk -F/ '{print $1}' | sed '/^$/d' | sort -u | head -n 30
