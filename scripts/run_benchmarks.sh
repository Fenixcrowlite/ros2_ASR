#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Build workspace and run benchmark runner once.
source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

mkdir -p results/plots

# Keep colcon isolated from venv site-packages injected via PYTHONPATH.
COLCON_PYTHONPATH="${PYTHONPATH-}"
PYTHONPATH="" colcon build --base-paths ros2_ws/src --symlink-install
if [ -n "${COLCON_PYTHONPATH}" ]; then
  export PYTHONPATH="${COLCON_PYTHONPATH}"
else
  unset PYTHONPATH
fi
set +u
source install/setup.bash
set -u

python3 -m asr_benchmark.runner \
  --config configs/default.yaml \
  --dataset data/transcripts/sample_manifest.csv \
  --output-json results/benchmark_results.json \
  --output-csv results/benchmark_results.csv
