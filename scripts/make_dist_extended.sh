#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f results/thesis_extended/manifest.json ]; then
  echo "ERROR: missing results/thesis_extended/manifest.json"
  exit 1
fi

mapfile -t EXT_ARTIFACTS < <(
  python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("results/thesis_extended/manifest.json").read_text(encoding="utf-8"))
for item in payload.get("canonical_artifacts", []):
    if item:
        print(item)
PY
)
mapfile -t BASELINE_ARTIFACTS < <(
  python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("results/thesis_final/manifest.json").read_text(encoding="utf-8"))
for item in payload.get("canonical_artifacts", []):
    if item:
        print(item)
PY
)

if [ "${#EXT_ARTIFACTS[@]}" -eq 0 ]; then
  echo "ERROR: no extended canonical artifacts listed"
  exit 1
fi

mkdir -p dist
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="dist/ros2_asr_thesis_extended_${TIMESTAMP}.tar.gz"

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
  --exclude='results/archive_legacy' \
  README.md THESIS_READER_GUIDE.md Makefile pyproject.toml requirements.txt requirements \
  docs ros2_ws/src scripts data/sample data/transcripts datasets configs tests \
  reports/datasets reports/thesis_test results/thesis_final results/thesis_extended results/runs_ext results/runs \
  "${BASELINE_ARTIFACTS[@]}" "${EXT_ARTIFACTS[@]}"

echo "Archive: $ARCHIVE"
echo "Size: $(du -h "$ARCHIVE" | awk '{print $1}')"
