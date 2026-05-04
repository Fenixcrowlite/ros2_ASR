#!/usr/bin/env bash
set -euo pipefail

# Package sterile release archive with required source/docs/results artifacts.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d "results/thesis_final/plots" ]; then
  echo "ERROR: results/thesis_final/plots is missing. Run scripts/export_thesis_tables.py from existing artifacts first."
  exit 1
fi

PLOT_COUNT=$(find results/thesis_final/plots -maxdepth 1 -name '*.png' | wc -l | tr -d ' ')
if [ "$PLOT_COUNT" -lt 8 ]; then
  echo "ERROR: expected 8 thesis plots in results/thesis_final/plots, found $PLOT_COUNT"
  exit 1
fi

mkdir -p dist
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="dist/ros2_asr_release_${TIMESTAMP}.tar.gz"
MANIFEST_PATH="results/thesis_final/manifest.json"
if [ ! -f "$MANIFEST_PATH" ]; then
  echo "ERROR: missing thesis manifest: $MANIFEST_PATH"
  exit 1
fi

mapfile -t FINAL_BENCHMARK_ARTIFACTS < <(
  python3 - <<'PY'
import json
from pathlib import Path

manifest = Path("results/thesis_final/manifest.json")
payload = json.loads(manifest.read_text(encoding="utf-8"))
for item in payload.get("canonical_artifacts", []):
    if item:
        print(item)
PY
)
if [ "${#FINAL_BENCHMARK_ARTIFACTS[@]}" -eq 0 ]; then
  echo "ERROR: no canonical_artifacts listed in $MANIFEST_PATH"
  exit 1
fi

for artifact_dir in "${FINAL_BENCHMARK_ARTIFACTS[@]}"; do
  for required_file in \
    metrics/results.json \
    metrics/results.csv \
    reports/summary.json \
    reports/summary.md \
    manifest/run_manifest.json; do
    if [ ! -f "$artifact_dir/$required_file" ]; then
      echo "ERROR: missing final benchmark artifact file: $artifact_dir/$required_file"
      exit 1
    fi
  done
done

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
  .ai/reports/current_task_report.md \
  data/sample \
  data/transcripts \
  datasets \
  configs \
  tests \
  reports/datasets \
  reports/thesis_test \
  results \
  "${FINAL_BENCHMARK_ARTIFACTS[@]}"

echo "Archive: $ARCHIVE"
echo "Size: $(du -h "$ARCHIVE" | awk '{print $1}')"
echo "Top-level entries:"
tar -tzf "$ARCHIVE" | awk -F/ '{print $1}' | sed '/^$/d' | sort -u | head -n 30
