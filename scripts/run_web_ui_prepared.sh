#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${ASR_PROVIDER_PROFILE:-providers/whisper_local}"
action="start"
args=("$@")

index=0
while [[ "$index" -lt "${#args[@]}" ]]; do
  case "${args[$index]}" in
    --provider-profile)
      index=$((index + 1))
      PROFILE="${args[$index]:-}"
      ;;
    --stop)
      action="stop"
      ;;
  esac
  index=$((index + 1))
done

if [[ "$action" == "start" ]]; then
  bash "$ROOT_DIR/scripts/prepare_provider_startup.sh" ui "$PROFILE"
fi

exec bash "$ROOT_DIR/scripts/run_web_ui.sh" "${args[@]}"
