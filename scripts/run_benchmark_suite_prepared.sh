#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${BENCHMARK_PROFILE:-default_benchmark}"
PROVIDERS_CSV=""
args=("$@")
index=0
while [[ "$index" -lt "${#args[@]}" ]]; do
  case "${args[$index]}" in
    --benchmark-profile)
      index=$((index + 1))
      PROFILE="${args[$index]:-}"
      ;;
    --providers)
      index=$((index + 1))
      PROVIDERS_CSV="${args[$index]:-}"
      ;;
    --skip-benchmark)
      exec bash "$ROOT_DIR/scripts/run_benchmark_suite.sh" "${args[@]}"
      ;;
  esac
  index=$((index + 1))
done

bash "$ROOT_DIR/scripts/prepare_benchmark_batch_startup.sh" "$PROFILE" "$PROVIDERS_CSV"
exec bash "$ROOT_DIR/scripts/run_benchmark_suite.sh" "${args[@]}"
