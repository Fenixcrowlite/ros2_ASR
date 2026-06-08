#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${1:-default_benchmark}"
PROVIDERS_CSV="${2:-}"

if [[ -n "$PROVIDERS_CSV" ]]; then
  IFS=',' read -r -a providers <<< "$PROVIDERS_CSV"
else
  mapfile -t providers < <(python3 scripts/list_benchmark_providers.py --profile "$PROFILE")
fi

if [[ "${#providers[@]}" -eq 0 ]]; then
  echo "ERROR: benchmark provider list is empty" >&2
  exit 1
fi

for provider in "${providers[@]}"; do
  provider="$(printf '%s' "$provider" | xargs)"
  [[ -n "$provider" ]] || continue
  echo "Preparing benchmark provider: $provider"
  bash scripts/prepare_provider_startup.sh runtime "$provider"
done
