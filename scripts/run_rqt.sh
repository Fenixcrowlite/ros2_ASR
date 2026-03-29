#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/source_runtime_env.sh" --with-ros

if ! command -v rqt >/dev/null 2>&1; then
  echo "ERROR: rqt is not installed or not visible in PATH after sourcing ROS Jazzy."
  exit 1
fi

check_env() {
  python3 - <<'PY'
import importlib

for module_name in ("asr_interfaces.msg", "asr_interfaces.srv"):
    importlib.import_module(module_name)

print("rqt environment ready: asr_interfaces Python modules are importable")
PY

  ros2 pkg prefix asr_interfaces >/dev/null
}

if [[ "${1:-}" == "--check-env" ]]; then
  check_env
  exit 0
fi

if ! check_env >/dev/null 2>&1; then
  echo "ERROR: rqt cannot resolve this workspace interfaces."
  echo "Run 'make build' first, then launch rqt via this script from the repo root."
  echo "Do not use a stale top-level 'install/setup.bash' overlay or a desktop launcher that does not source the workspace."
  exit 1
fi

if [[ "$#" -eq 0 ]]; then
  exec rqt --standalone rqt_topic
fi

exec rqt "$@"
