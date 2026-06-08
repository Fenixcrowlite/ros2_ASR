#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-runtime}"
PROFILE="${2:-providers/whisper_local}"

prepare_vosk_if_needed() {
  local profile="$1"
  if [[ "$profile" == "providers/vosk_local" ]]; then
    bash "$ROOT_DIR/scripts/maintenance/setup_vosk_models.sh"
  fi
}

prepare_selected_provider() {
  local profile="$1"
  prepare_vosk_if_needed "$profile"
  bash "$ROOT_DIR/scripts/init_provider_env.sh" --prompt-provider "$profile"
  bash "$ROOT_DIR/scripts/run_provider_preflight.sh" "$profile"
}

case "$MODE" in
  ui)
    # The browser UI exposes Vosk after launch, so make its local assets usable
    # before the operator can select it. Cloud credentials remain optional and
    # may be skipped during the first-run walkthrough.
    bash "$ROOT_DIR/scripts/maintenance/setup_vosk_models.sh"
    bash "$ROOT_DIR/scripts/init_provider_env.sh" --prompt-missing-once
    prepare_selected_provider "$PROFILE"
    ;;
  runtime)
    prepare_selected_provider "$PROFILE"
    ;;
  *)
    echo "ERROR: unsupported provider startup mode: $MODE" >&2
    exit 1
    ;;
esac
