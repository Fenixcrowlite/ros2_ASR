#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TEMPLATE="configs/runtime.env.example"
TARGET="secrets/local/runtime.env"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Missing tracked template: $TEMPLATE" >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"

if [[ -e "$TARGET" ]]; then
  chmod 600 "$TARGET"
  echo "Provider environment file already exists; keeping current values: $TARGET"
  echo "Edit it manually when needed."
  exit 0
fi

cp "$TEMPLATE" "$TARGET"
chmod 600 "$TARGET"

echo "Created provider environment file from the safe template: $TARGET"
echo "Fill only the providers you use and keep unused values empty."
echo "Provider setup guide: docs/provider_env.md"
