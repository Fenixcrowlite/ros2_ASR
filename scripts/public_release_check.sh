#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

warn() {
  echo "WARN: $1" >&2
}

echo "[public-release-check] documentation consistency"
make docs-check

echo "[public-release-check] secret scan"
bash scripts/secret_scan.sh

echo "[public-release-check] dataset registry portability"
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .

echo "[public-release-check] tracked local credential paths"
tracked_local_credentials="$(git ls-files -- \
  'secrets/local/**' \
  'secrets/google/**' \
  '*.pem' \
  '*.key' \
  '*.p12' \
  '*service-account*.json' \
  '*credentials*.json' || true)"
if [[ -n "$tracked_local_credentials" ]]; then
  echo "$tracked_local_credentials" >&2
  fail "local credential material or private key files are tracked"
fi

echo "[public-release-check] safe environment template"
[[ -f configs/runtime.env.example ]] || fail "missing configs/runtime.env.example"
if grep -Eq '^[A-Za-z_][A-Za-z0-9_]*=.+$' configs/runtime.env.example; then
  fail "configs/runtime.env.example contains populated values"
fi

echo "[public-release-check] repository status"
if [[ -n "$(git status --short)" ]]; then
  warn "working tree contains local changes; review git status before publishing"
  git status --short
fi

echo "PASS: static public repository checks completed"
echo "NOTE: run the clean-clone, build, runtime, and provider-specific checks from docs/public_release_checklist.md before sharing the repository."
