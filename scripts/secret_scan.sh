#!/usr/bin/env bash
set -euo pipefail

# Preflight scan for accidentally tracked secrets before release packaging.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SECRET_REGEX="AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN[[:space:]]+[^-]*PRIVATE KEY-----|aws_secret_access_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9/+=]{16,}|speech_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|subscription_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|xox[baprs]-[0-9A-Za-z-]{10,}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  mapfile -d '' SCAN_FILES < <(
    {
      git ls-files -z
      find reports results artifacts .ai scripts configs datasets -type f -print0 2>/dev/null || true
    } | sort -zu
  )
else
  mapfile -d '' SCAN_FILES < <(
    find . -type f \
      -not -path './.git/*' \
      -not -path './.venv/*' \
      -not -path './venv/*' \
      -not -path './__pycache__/*' \
      -print0
  )
fi
FINDINGS=()

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
  done < <(grep -nEI "$SECRET_REGEX" "$file" || true)
done

if [ "${#FINDINGS[@]}" -gt 0 ]; then
  echo "FAIL: potential secrets detected:"
  printf ' - %s\n' "${FINDINGS[@]}"
  exit 1
fi

echo "PASS: no obvious secrets found"
