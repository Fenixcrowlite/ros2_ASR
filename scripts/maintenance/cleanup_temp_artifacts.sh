#!/usr/bin/env bash
set -euo pipefail

find artifacts/temp -mindepth 1 -maxdepth 1 -type d -print -exec rm -rf {} +
