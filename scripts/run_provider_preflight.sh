#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${1:-providers/whisper_local}"
source "$ROOT_DIR/scripts/source_runtime_env.sh" --without-ros
python3 "$ROOT_DIR/scripts/provider_preflight.py" --profile "$PROFILE"
