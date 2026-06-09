#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${BENCHMARK_PROFILE:-default_benchmark}"
bash "$ROOT_DIR/scripts/prepare_benchmark_batch_startup.sh" "$PROFILE"
exec bash "$ROOT_DIR/scripts/run_benchmarks.sh"
