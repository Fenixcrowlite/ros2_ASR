#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $1"
  exit 1
}

echo "[release-check] running unit tests"
make test-unit

echo "[release-check] running benchmark"
make bench

echo "[release-check] verifying artifacts"
shopt -s nullglob
csv_files=(results/*.csv)
json_files=(results/*.json)
plot_files=(results/plots/*.png)

(( ${#csv_files[@]} > 0 )) || fail "missing results/*.csv"
(( ${#json_files[@]} > 0 )) || fail "missing results/*.json"
(( ${#plot_files[@]} >= 3 )) || fail "expected >=3 plots in results/plots"

echo "PASS"
