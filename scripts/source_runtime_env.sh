#!/usr/bin/env bash
# shellcheck shell=bash

# Source project runtime environment in current shell.
# Usage:
#   source scripts/source_runtime_env.sh --without-ros
#   source scripts/source_runtime_env.sh --with-ros

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "ERROR: this script must be sourced, not executed."
  echo "Use: source scripts/source_runtime_env.sh [--with-ros|--without-ros]"
  exit 1
fi

_with_ros=0
case "${1:---without-ros}" in
  --with-ros)
    _with_ros=1
    ;;
  --without-ros | "")
    ;;
  *)
    echo "[env] WARN: unknown argument '$1', expected --with-ros or --without-ros"
    ;;
esac

_root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

_prepend_unique_path() {
  local _candidate="$1"
  local _current="${2:-}"
  if [ -z "$_candidate" ]; then
    printf "%s" "$_current"
    return
  fi
  case ":${_current}:" in
    *":${_candidate}:"*)
      printf "%s" "$_current"
      ;;
    *)
      if [ -n "$_current" ]; then
        printf "%s:%s" "$_candidate" "$_current"
      else
        printf "%s" "$_candidate"
      fi
      ;;
  esac
}

if [ -f "$_root_dir/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$_root_dir/.venv/bin/activate"
else
  echo "[env] WARN: .venv not found at $_root_dir/.venv"
fi

if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "${VIRTUAL_ENV}/bin/python3" ]; then
  _venv_site_packages="$("${VIRTUAL_ENV}/bin/python3" - <<'PY'
import site

paths = [item for item in site.getsitepackages() if "site-packages" in item]
print(paths[0] if paths else "")
PY
)"
  if [ -n "$_venv_site_packages" ]; then
    export PYTHONPATH="$(_prepend_unique_path "$_venv_site_packages" "${PYTHONPATH:-}")"
  fi

  # Ensure CUDA runtime libs from pip nvidia wheels are discoverable.
  while IFS= read -r _cuda_lib_dir; do
    [ -n "$_cuda_lib_dir" ] || continue
    export LD_LIBRARY_PATH="$(_prepend_unique_path "$_cuda_lib_dir" "${LD_LIBRARY_PATH:-}")"
  done < <("${VIRTUAL_ENV}/bin/python3" - <<'PY'
import glob
import os
import site

paths: list[str] = []
for base in site.getsitepackages():
    paths.extend(glob.glob(os.path.join(base, "nvidia", "*", "lib")))
for item in sorted(set(paths)):
    print(item)
PY
)
fi

while IFS= read -r _pkg_dir; do
  [ -n "$_pkg_dir" ] || continue
  export PYTHONPATH="$(_prepend_unique_path "$_pkg_dir" "${PYTHONPATH:-}")"
done < <(find "$_root_dir/ros2_ws/src" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)

if [ "$_with_ros" -eq 1 ]; then
  _nounset_was_on=0
  case "$-" in
    *u*)
      _nounset_was_on=1
      set +u
      ;;
  esac

  if [ -f /opt/ros/jazzy/setup.bash ]; then
    # shellcheck disable=SC1091
    source /opt/ros/jazzy/setup.bash
    if [ -f "$_root_dir/install/setup.bash" ]; then
      # shellcheck disable=SC1091
      source "$_root_dir/install/setup.bash"
    fi
  else
    echo "[env] WARN: /opt/ros/jazzy/setup.bash not found"
  fi

  if [ "$_nounset_was_on" -eq 1 ]; then
    set -u
  fi
fi
