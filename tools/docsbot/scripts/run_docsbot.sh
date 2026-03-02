#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TOOL_DIR="$REPO_ROOT/tools/docsbot"
TOOL_VENV="$TOOL_DIR/.venv"
ROOT_VENV="$REPO_ROOT/.venv"

if [ -x "$TOOL_VENV/bin/docsbot" ]; then
  DOCSBOT_BIN="$TOOL_VENV/bin/docsbot"
else
  if [ ! -d "$TOOL_VENV" ]; then
    if ! python3 -m venv "$TOOL_VENV" >/dev/null 2>&1; then
      # Ubuntu minimal images can miss python3-venv/ensurepip.
      mkdir -p "$TOOL_VENV"
    fi
  fi

  if [ -x "$TOOL_VENV/bin/pip" ]; then
    source "$TOOL_VENV/bin/activate"
    pip install -q -U pip
    pip install -q -e "$TOOL_DIR[dev]"
    DOCSBOT_BIN="$TOOL_VENV/bin/docsbot"
  elif [ -x "$ROOT_VENV/bin/docsbot" ]; then
    DOCSBOT_BIN="$ROOT_VENV/bin/docsbot"
  elif [ -x "$ROOT_VENV/bin/pip" ]; then
    source "$ROOT_VENV/bin/activate"
    pip install -q -e "$TOOL_DIR[dev]"
    DOCSBOT_BIN="$ROOT_VENV/bin/docsbot"
  else
    python3 -m pip install --user -q -e "$TOOL_DIR[dev]"
    DOCSBOT_BIN="$(python3 -c 'import os,site; print(os.path.join(site.USER_BASE, \"bin\", \"docsbot\"))')"
  fi
fi

cd "$REPO_ROOT"
"$DOCSBOT_BIN" "$@"
