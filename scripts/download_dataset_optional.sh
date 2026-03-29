#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "$ROOT_DIR/.venv/bin/activate" ]]; then
  echo ".venv missing. Run make setup first." >&2
  exit 1
fi

source "$ROOT_DIR/.venv/bin/activate"
python "$ROOT_DIR/scripts/import_dataset/build_external_subsets.py" "$@"
