#!/usr/bin/env bash
set -euo pipefail

# Preflight scan for accidentally tracked secrets before release packaging.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SECRET_REGEX="AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN[[:space:]]+[^-]*PRIVATE KEY-----|aws_secret_access_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9/+=]{16,}|speech_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|subscription_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|xox[baprs]-[0-9A-Za-z-]{10,}"

SCAN_ROOTS=(.ai reports results scripts configs datasets docs)
EXCLUDE_NAME_EXPR=(
  -name '*.wav' -o -name '*.mp3' -o -name '*.flac' -o
  -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.gif' -o -name '*.webp' -o
  -name '*.onnx' -o -name '*.pt' -o -name '*.pth' -o -name '*.bin' -o -name '*.safetensors'
)
mapfile -d '' SCAN_FILES < <(
  find "${SCAN_ROOTS[@]}" -type f \
    -not -path 'artifacts/benchmark_runs/*/derived_audio/*' \
    -not -path 'secrets/*' \
    -not -path '*/__pycache__/*' \
    -not \( "${EXCLUDE_NAME_EXPR[@]}" \) \
    -print0 2>/dev/null | sort -z
)
FINDINGS=()
SCANNED_COUNT=0

for file in "${SCAN_FILES[@]}"; do
  file="${file#./}"
  [[ "$file" == configs/*.example.* ]] && continue
  [[ "$file" == */*.example.* ]] && continue
  [[ "$file" == dist/* ]] && continue
  [[ "$file" == .git/* ]] && continue
  [[ "$file" == .venv/* ]] && continue
  [[ "$file" == venv/* ]] && continue
  [[ "$file" == secrets/* ]] && continue
  [[ -f "$file" ]] || continue
  SCANNED_COUNT=$((SCANNED_COUNT + 1))

  if [[ "$file" == ".env" || "$file" =~ \.env$ ]]; then
    FINDINGS+=("tracked env file path: $file")
  fi
  if [[ "$file" =~ \.(pem|p12|key)$ ]]; then
    FINDINGS+=("tracked key-like file path: $file")
  fi
  if [[ "$file" =~ [Ss]ervice.?[Aa]ccount.*\.json$ ]]; then
    FINDINGS+=("tracked service-account json file path: $file")
  fi

  while IFS= read -r hit; do
    FINDINGS+=("$file:$hit")
  done < <(grep -nEIH "$SECRET_REGEX" "$file" || true)
done

echo "Scanned files: $SCANNED_COUNT"

if [ "${#FINDINGS[@]}" -gt 0 ]; then
  echo "FAIL: potential secrets detected:"
  printf ' - %s\n' "${FINDINGS[@]}"
  exit 1
fi

echo "PASS: no obvious secrets found"
