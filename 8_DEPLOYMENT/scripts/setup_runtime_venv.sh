#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RUNTIME_DIR="${CLARA_RUNTIME_DIR:-$HOME/.clara_runtime}"
VENV_DIR="$RUNTIME_DIR/venv"

mkdir -p "$RUNTIME_DIR"
bash "$SCRIPT_DIR/sync_runtime_app.sh"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install -r "$RUNTIME_DIR/app/8_DEPLOYMENT/requirements.txt"

echo "Runtime venv ready at: $VENV_DIR"
