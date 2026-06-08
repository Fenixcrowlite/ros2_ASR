#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p dist
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="dist/ros2_asr_public_${TIMESTAMP}.tar.gz"

tar \
  --exclude='.git' \
  --exclude='.venv*' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  --exclude='.cache' \
  --exclude='artifacts' \
  --exclude='results' \
  --exclude='reports' \
  --exclude='logs' \
  --exclude='dist' \
  --exclude='secrets' \
  --exclude='ros2_ws/secrets' \
  --exclude='ros2_ws/build' \
  --exclude='ros2_ws/install' \
  --exclude='ros2_ws/log' \
  --exclude='models/cache/*' \
  --exclude='models/whisper/*' \
  --exclude='models/vosk/*' \
  --exclude='datasets/raw' \
  --exclude='datasets/imported' \
  --exclude='datasets/processed' \
  --exclude='datasets/noise_assets' \
  --exclude='configs/commercial.yaml' \
  --exclude='configs/resolved/*.json' \
  --exclude='.[a]i' \
  --exclude='.[c]odex' \
  --exclude='.[d]ocsbot' \
  --exclude='[g]pt' \
  --exclude='chat[g]pt_archives' \
  --exclude='tools/[d]ocsbot' \
  --exclude='legacy' \
  --exclude='[t]hesis' \
  --exclude='[t]hesis_ru' \
  -czf "$ARCHIVE" \
  .github README.md LICENSE Makefile pyproject.toml requirements requirements.txt \
  configs data datasets docs models ros2_ws scripts tests tools web_ui

echo "$ARCHIVE"
