#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TEMPLATE="configs/runtime.env.example"
TARGET="secrets/local/runtime.env"
PROMPTED_MARKER="secrets/local/.provider_setup_prompted"
MODE="${1:---init}"
SELECTED_PROVIDER="${2:-}"

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

ensure_env_file() {
  [[ -f "$TEMPLATE" ]] || fail "Missing tracked template: $TEMPLATE"
  mkdir -p "$(dirname "$TARGET")"
  if [[ ! -e "$TARGET" ]]; then
    cp "$TEMPLATE" "$TARGET"
    echo "Created provider environment file from the safe template: $TARGET"
  fi
  chmod 600 "$TARGET"
}

get_value() {
  local key="$1"
  local line=""
  line="$(grep -E "^${key}=" "$TARGET" | tail -n 1 || true)"
  printf '%s' "${line#*=}"
}

set_value() {
  local key="$1"
  local value="$2"
  printf '%s' "$value" | python3 -c '
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.stdin.read()
lines = path.read_text(encoding="utf-8").splitlines()
replacement = f"{key}={value}"
for index, line in enumerate(lines):
    if line.startswith(f"{key}="):
        lines[index] = replacement
        break
else:
    lines.extend(["", replacement])
path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
' "$TARGET" "$key"
  chmod 600 "$TARGET"
}

is_interactive() {
  [[ -t 0 && -t 1 ]]
}

ask_choice() {
  local prompt="$1"
  local answer=""
  read -r -p "$prompt" answer
  printf '%s' "${answer,,}"
}

prompt_value() {
  local key="$1"
  local label="$2"
  local secret="${3:-0}"
  local required="${4:-1}"
  local existing=""
  local answer=""
  local value=""
  local normalized_value=""

  existing="$(get_value "$key")"
  if [[ -n "$existing" ]]; then
    echo "  configured: $key"
    return 0
  fi

  if ! is_interactive; then
    if [[ "$required" == "1" ]]; then
      echo "  missing: $key (non-interactive run; configure later with: make configure-providers)"
    fi
    return 0
  fi

  while true; do
    answer="$(ask_choice "  $label is missing. Configure it now? [y/N/s=skip]: ")"
    case "$answer" in
      y|yes)
        ;;
      s|skip|n|no|"")
        echo "  skipped: $key"
        return 0
        ;;
      *)
        echo "  skipped: $key (unrecognized answer)"
        return 0
        ;;
    esac

    if [[ "$secret" == "1" ]]; then
      read -r -s -p "  Enter $label ([b] back): " value
      echo
    else
      read -r -p "  Enter $label ([b] back): " value
    fi

    normalized_value="${value,,}"
    if [[ "$normalized_value" == "b" || "$normalized_value" == "back" ]]; then
      echo "  back: returning to the previous choice for $key"
      continue
    fi

    if [[ -z "$value" ]]; then
      echo "  skipped: $key (empty value)"
      return 0
    fi

    set_value "$key" "$value"
    echo "  saved locally: $key"
    return 0
  done
}

prompt_huggingface_api() {
  echo
  echo "Hugging Face hosted API"
  prompt_value "HF_TOKEN" "Hugging Face access token" 1 1
}

prompt_huggingface_local() {
  echo
  echo "Hugging Face local"
  echo "  Public models need no token. Private or gated models may require one."
  prompt_value "HF_TOKEN" "optional Hugging Face access token" 1 0
}

prompt_azure() {
  echo
  echo "Azure Speech"
  prompt_value "AZURE_SPEECH_KEY" "Azure Speech key" 1 1
  prompt_value "AZURE_SPEECH_REGION" "Azure Speech region" 0 1
}

prompt_google() {
  echo
  echo "Google Cloud Speech-to-Text"
  echo "  Skip the JSON path when Application Default Credentials are already configured."
  prompt_value "GOOGLE_APPLICATION_CREDENTIALS" "path to Google service-account JSON" 0 0
  prompt_value "GOOGLE_CLOUD_PROJECT" "optional Google Cloud project ID" 0 0
}

prompt_aws() {
  local answer=""
  echo
  echo "Amazon Transcribe"

  if [[ -z "$(get_value AWS_PROFILE)" && -z "$(get_value AWS_ACCESS_KEY_ID)" ]]; then
    if is_interactive; then
      answer="$(ask_choice "  Choose AWS authentication: [1] CLI profile, [2] access keys, [s] skip: ")"
      case "$answer" in
        1|profile)
          prompt_value "AWS_PROFILE" "AWS CLI profile" 0 1
          ;;
        2|keys)
          prompt_value "AWS_ACCESS_KEY_ID" "AWS access key ID" 0 1
          prompt_value "AWS_SECRET_ACCESS_KEY" "AWS secret access key" 1 1
          prompt_value "AWS_SESSION_TOKEN" "optional AWS session token" 1 0
          ;;
        *)
          echo "  skipped: AWS authentication"
          ;;
      esac
    else
      echo "  missing: AWS authentication (non-interactive run; configure later with: make configure-providers)"
    fi
  else
    echo "  configured: AWS authentication"
  fi

  prompt_value "AWS_REGION" "AWS region" 0 1
  prompt_value "AWS_S3_BUCKET" "writable S3 bucket for Transcribe jobs" 0 1
}

prompt_provider() {
  local profile="$1"
  case "$profile" in
    providers/whisper_local|providers/vosk_local|"")
      ;;
    providers/huggingface_local)
      prompt_huggingface_local
      ;;
    providers/huggingface_api)
      prompt_huggingface_api
      ;;
    providers/azure_cloud)
      prompt_azure
      ;;
    providers/google_cloud)
      prompt_google
      ;;
    providers/aws_cloud)
      prompt_aws
      ;;
    *)
      echo "No interactive setup rules for provider profile: $profile"
      ;;
  esac
}

prompt_all() {
  echo
  echo "Optional provider configuration walkthrough"
  echo "You can skip any provider and configure it later with: make configure-providers"
  echo "After choosing configure, enter b to go back without saving a value."
  prompt_huggingface_local
  prompt_huggingface_api
  prompt_azure
  prompt_google
  prompt_aws
}

ensure_env_file

case "$MODE" in
  --init)
    echo "Provider environment file is ready: $TARGET"
    echo "Edit it manually or run: make configure-providers"
    ;;
  --prompt-all)
    prompt_all
    touch "$PROMPTED_MARKER"
    ;;
  --prompt-missing-once)
    if [[ ! -e "$PROMPTED_MARKER" ]]; then
      if is_interactive; then
        prompt_all
        touch "$PROMPTED_MARKER"
      else
        echo "Skipping optional provider walkthrough in non-interactive mode."
      fi
    fi
    ;;
  --prompt-provider)
    prompt_provider "$SELECTED_PROVIDER"
    ;;
  *)
    fail "Unknown mode: $MODE"
    ;;
esac
