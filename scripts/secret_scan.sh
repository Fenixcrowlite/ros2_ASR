#!/usr/bin/env bash
set -euo pipefail

# Preflight scan for accidentally tracked secrets before release packaging.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL: secret scan requires a git repository (tracked files scan)."
  exit 1
fi

SECRET_REGEX="AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN[[:space:]]+[^-]*PRIVATE KEY-----|aws_secret_access_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9/+=]{16,}|speech_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|subscription_key[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9]{16,}|xox[baprs]-[0-9A-Za-z-]{10,}|\"type\"[[:space:]]*:[[:space:]]*\"service_account\""

mapfile -d '' TRACKED_FILES < <(git ls-files -z)
FINDINGS=()

for file in "${TRACKED_FILES[@]}"; do
  [[ "$file" == configs/*.example.* ]] && continue
  [[ "$file" == */*.example.* ]] && continue
  [[ "$file" == dist/* ]] && continue
  [[ -f "$file" ]] || continue

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
  echo "FAIL: potential secrets detected in tracked files:"
  printf ' - %s\n' "${FINDINGS[@]}"
  exit 1
fi

echo "PASS: no obvious secrets found in tracked files"
