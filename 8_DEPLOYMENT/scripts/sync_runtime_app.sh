#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_ROOT_DIR="$(cd "$SOURCE_DEPLOY_DIR/.." && pwd)"

RUNTIME_DIR="${CLARA_RUNTIME_DIR:-$HOME/.clara_runtime}"
RUNTIME_APP_DIR="$RUNTIME_DIR/app"
RUNTIME_DEPLOY_DIR="$RUNTIME_APP_DIR/8_DEPLOYMENT"

mkdir -p "$RUNTIME_APP_DIR"

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude "venv/" \
  --exclude "logs/" \
  --exclude "6_CORPUS/**/Media/" \
  "$SOURCE_ROOT_DIR/1_PROMPTS/" "$RUNTIME_APP_DIR/1_PROMPTS/"

# Optional large corpus sync (can take a long time).
if [[ "${CLARA_SYNC_CORPUS:-0}" == "1" ]]; then
  rsync -a --delete \
    --exclude ".git/" \
    --exclude ".venv/" \
    --exclude "venv/" \
    --exclude "logs/" \
    --exclude "6_CORPUS/**/Media/" \
    "$SOURCE_ROOT_DIR/6_CORPUS/" "$RUNTIME_APP_DIR/6_CORPUS/"
else
  mkdir -p "$RUNTIME_APP_DIR/6_CORPUS"
fi

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude "venv/" \
  --exclude "__pycache__/" \
  "$SOURCE_ROOT_DIR/8_DEPLOYMENT/" "$RUNTIME_APP_DIR/8_DEPLOYMENT/"

if [[ -f "$SOURCE_DEPLOY_DIR/.env" ]]; then
  cp "$SOURCE_DEPLOY_DIR/.env" "$RUNTIME_DEPLOY_DIR/.env"
fi

echo "Runtime app synced to: $RUNTIME_APP_DIR"
if [[ "${CLARA_SYNC_CORPUS:-0}" != "1" ]]; then
  echo "Skipped corpus sync. Set CLARA_SYNC_CORPUS=1 to fully mirror 6_CORPUS."
fi
