#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Create local virtual environment and install Python dependencies.
if [ ! -d .venv ]; then
  if ! python3 -m venv .venv 2>/dev/null; then
    echo "python3 -m venv failed, trying virtualenv fallback"
    python3 -m pip install --user --break-system-packages virtualenv
    python3 -m virtualenv .venv
  fi
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ln -sf "$(pwd)/archviz" .venv/bin/archviz

echo
echo "Environment ready."
echo "Next steps for the default local Whisper run:"
echo "  make build"
echo "  make up"
echo
echo "Open the browser UI at: http://127.0.0.1:8088"
echo
echo "Optional verification and maintenance commands:"
echo "  make test-gateway-smoke"
echo "  make docs-check"
echo "  make validate-datasets"
echo "  make public-release-check"
echo
echo "For cloud or hosted providers, create the local environment file safely:"
echo "  make init-provider-env"
echo
echo "Provider activation guide: docs/asr_backends.md"
echo "Provider environment guide: docs/provider_env.md"
echo "Provider-specific CLI checks: docs/provider_cli.md"
