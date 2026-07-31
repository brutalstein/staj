#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ "$#" -eq 0 ]]; then
  set -- start
fi
exec "$PYTHON_BIN" tools/project_launcher.py "$@"
