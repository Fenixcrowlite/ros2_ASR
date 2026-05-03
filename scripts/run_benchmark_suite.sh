#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SCENARIO="embedded"
NORMALIZATION_PROFILE="normalized-v1"
BENCHMARK_PROFILE="${BENCHMARK_PROFILE:-default_benchmark}"
DATASET_PROFILE=""
PROVIDERS=""
RUN_ID=""
CONFIGS_ROOT="$ROOT_DIR/configs"
ARTIFACT_ROOT="$ROOT_DIR/artifacts"
REGISTRY_PATH="$ROOT_DIR/datasets/registry/datasets.json"
RESULTS_DIR="$ROOT_DIR/results"
INPUT_PATH=""
VOCABULARY_FILE=""
ENERGY_J=""
SKIP_BENCHMARK=0
NO_PLOTS=0

usage() {
  cat <<'EOF'
Usage: scripts/run_benchmark_suite.sh [options]

Runs the existing benchmark core, then builds schema-first thesis artifacts in
results/runs/<run_id>/ via scripts/collect_metrics.py.

Options:
  --scenario embedded|batch|analytics|dialog
  --normalization-profile NAME
  --benchmark-profile NAME
  --dataset-profile NAME
  --providers providers/a,providers/b
  --run-id RUN_ID
  --configs-root PATH
  --artifact-root PATH
  --registry-path PATH
  --results-dir PATH
  --input PATH              Existing canonical/legacy/schema input for --skip-benchmark
  --vocabulary-file PATH    Optional vocabulary for OOV rate
  --energy-j VALUE          Optional total measured energy for the run
  --skip-benchmark          Only collect schema-first artifacts from --input/default results
  --no-plots
  -h, --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario)
      SCENARIO="$2"
      shift 2
      ;;
    --normalization-profile)
      NORMALIZATION_PROFILE="$2"
      shift 2
      ;;
    --benchmark-profile)
      BENCHMARK_PROFILE="$2"
      shift 2
      ;;
    --dataset-profile)
      DATASET_PROFILE="$2"
      shift 2
      ;;
    --providers)
      PROVIDERS="$2"
      shift 2
      ;;
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --configs-root)
      CONFIGS_ROOT="$2"
      shift 2
      ;;
    --artifact-root)
      ARTIFACT_ROOT="$2"
      shift 2
      ;;
    --registry-path)
      REGISTRY_PATH="$2"
      shift 2
      ;;
    --results-dir)
      RESULTS_DIR="$2"
      shift 2
      ;;
    --input)
      INPUT_PATH="$2"
      shift 2
      ;;
    --vocabulary-file)
      VOCABULARY_FILE="$2"
      shift 2
      ;;
    --energy-j)
      ENERGY_J="$2"
      shift 2
      ;;
    --skip-benchmark)
      SKIP_BENCHMARK=1
      shift
      ;;
    --no-plots)
      NO_PLOTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for required in scripts/run_benchmark_core.py scripts/collect_metrics.py; do
  if [[ ! -f "$ROOT_DIR/$required" ]]; then
    echo "Required benchmark artifact is missing: $required" >&2
    exit 1
  fi
done

if [[ "$SKIP_BENCHMARK" -eq 0 ]]; then
  source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

  BENCH_ARGS=(
    python3 scripts/run_benchmark_core.py
    --benchmark-profile "$BENCHMARK_PROFILE"
    --configs-root "$CONFIGS_ROOT"
    --artifact-root "$ARTIFACT_ROOT"
    --registry-path "$REGISTRY_PATH"
    --results-dir "$RESULTS_DIR"
  )
  if [[ -n "$DATASET_PROFILE" ]]; then
    BENCH_ARGS+=(--dataset-profile "$DATASET_PROFILE")
  fi
  if [[ -n "$PROVIDERS" ]]; then
    BENCH_ARGS+=(--providers "$PROVIDERS")
  fi
  if [[ -n "$RUN_ID" ]]; then
    BENCH_ARGS+=(--run-id "$RUN_ID")
  fi
  "${BENCH_ARGS[@]}"

  INPUT_PATH="$RESULTS_DIR/latest_benchmark_summary.json"
else
  if [[ -z "$INPUT_PATH" ]]; then
    INPUT_PATH="$RESULTS_DIR/latest_benchmark_summary.json"
  fi
fi

COLLECT_ARGS=(
  python3 scripts/collect_metrics.py
  --input "$INPUT_PATH"
  --scenario "$SCENARIO"
  --normalization-profile "$NORMALIZATION_PROFILE"
  --results-dir "$RESULTS_DIR"
  --artifact-root "$ARTIFACT_ROOT"
)
if [[ -n "$RUN_ID" ]]; then
  COLLECT_ARGS+=(--run-id "$RUN_ID")
fi
if [[ -n "$VOCABULARY_FILE" ]]; then
  COLLECT_ARGS+=(--vocabulary-file "$VOCABULARY_FILE")
fi
if [[ -n "$ENERGY_J" ]]; then
  COLLECT_ARGS+=(--energy-j "$ENERGY_J")
fi
if [[ "$NO_PLOTS" -eq 1 ]]; then
  COLLECT_ARGS+=(--no-plots)
fi

"${COLLECT_ARGS[@]}"
