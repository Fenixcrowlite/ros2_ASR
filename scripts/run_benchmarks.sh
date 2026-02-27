#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/jazzy/setup.bash
set -u

mkdir -p results/plots

colcon build --base-paths ros2_ws/src --symlink-install
set +u
source install/setup.bash
set -u
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

python3 -m asr_benchmark.runner \
  --config configs/default.yaml \
  --dataset data/transcripts/sample_manifest.csv \
  --output-json results/benchmark_results.json \
  --output-csv results/benchmark_results.csv
